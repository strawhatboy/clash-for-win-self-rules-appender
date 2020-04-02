
import watchdog.observers
import watchdog.events
import yaml
import os
import sys
import pathlib
import argparse
import time
t_start = time.time()


class RuleAppender:

    target_file = ''
    is_direct_update = False

    def on_created_func(event):
        print('file created: {}'.format(event.src_path))
        # merge it with ours
        print('Updating...')

        myconf = yaml.load(open('myconf.yml', 'r'), Loader=yaml.CLoader)
        newconf = yaml.load(open(event.src_path, 'r'), Loader=yaml.CLoader)
        newconf['Rule'] = myconf['Rule'] + newconf['Rule']

        if RuleAppender.is_direct_update:
            file_to_be_update = event.src_path
        else:
            file_to_be_update = RuleAppender.target_file

        with open(file_to_be_update, 'w') as f:
            f.write(yaml.dump(newconf, Dumper=yaml.CDumper))
            f.flush()
            print('Successfully updated config file {}'.format(
                file_to_be_update))

    def main(argvs):
        parser = argparse.ArgumentParser()

        parser.add_argument(
            '-d', '--direct', action='store_true', help='switch on to directly modify the subscribed config, if leave it off, you need to specify a custom config path to "--config"')
        parser.add_argument(
            '-c', '--config', default='', help='when "--direct" is not enabled, this file will be written, you can locate it by clicking \'Edit in Text Mode\' on your CFW config')
        parser.add_argument(
            '-p', '--profile-dir', default='', help='directory for profiles, if empty, will try to extract from "--config", can also be useful if you\'re in Windows Subsystem Linux')
        argv = parser.parse_args(argvs)

        if argv.direct:
            RuleAppender.is_direct_update = True
            print('Will update subscribed config directly, Simple & Effective')

            if argv.profile_dir != '' and os.path.exists(argv.profile_dir):
                filepath = argv.profile_dir
            else:
                # get current user's profiles path
                filepath = os.path.join(pathlib.Path.home(),
                                        '.config', 'clash', 'profiles')

        elif argv.config != '':
            if os.path.exists(argv.config):
                RuleAppender.target_file = argv.config
                filepath = os.path.dirname(argv.config)
            else:
                print('Error: file {} not exist'.format(argv.config))
                return

        else:
            print('Error: "--config" should be specified if "--direct" is off')
            return

        handler = watchdog.events.PatternMatchingEventHandler(patterns='*.yml')
        handler.on_created = RuleAppender.on_created_func

        observer = watchdog.observers.Observer()
        observer.schedule(handler, filepath)
        observer.start()
        print('Listening updates from {}...'.format(filepath))

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            observer.join()
        pass


if __name__ == "__main__":
    RuleAppender.main(sys.argv[1:])
    t_end = time.time()
    print('Script finished in {} s'.format(t_end-t_start))

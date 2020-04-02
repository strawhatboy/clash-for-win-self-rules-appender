
import yaml
import argparse
import contextlib
import os
import pathlib
import sys
import time
import watchdog.observers
import watchdog.events
t_start = time.time()

# copied from https://stackoverflow.com/questions/18781239/python-watchdog-is-there-a-way-to-pause-the-observer
class PausingObserver(watchdog.observers.Observer):
    def dispatch_events(self, *args, **kwargs):
        if not getattr(self, '_is_paused', False):
            super(PausingObserver, self).dispatch_events(*args, **kwargs)

    def pause(self):
        self._is_paused = True

    def resume(self):
        time.sleep(self.timeout)  # allow interim events to be queued
        self.event_queue.queue.clear()
        self._is_paused = False

    @contextlib.contextmanager
    def ignore_events(self):
        self.pause()
        yield
        self.resume()


class RuleAppender:

    observer = None
    target_file = ''
    is_direct_update = False

    @staticmethod
    def on_created_func(event):
        print('file created: {}'.format(event.src_path))
        with RuleAppender.observer.ignore_events():
            RuleAppender.append_to_file(event)

    @staticmethod
    def on_modified_func(event):
        if os.path.isdir(event.src_path):
            # ignore dir event
            return

        print('file modified: {}, could be an automatic update'.format(event.src_path))
        with RuleAppender.observer.ignore_events():
            RuleAppender.append_to_file(event)

    @staticmethod
    def append_to_file(event):
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

    @staticmethod
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

        handler = watchdog.events.RegexMatchingEventHandler(
            regexes=['.*(?<!list\\.yml)$'])
        handler.on_created = RuleAppender.on_created_func
        handler.on_modified = RuleAppender.on_modified_func

        RuleAppender.observer = PausingObserver()
        RuleAppender.observer.schedule(handler, filepath)
        RuleAppender.observer.start()
        print('Listening updates from {}...'.format(filepath))

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            RuleAppender.observer.stop()
            RuleAppender.observer.join()
        pass


if __name__ == "__main__":
    RuleAppender.main(sys.argv[1:])
    t_end = time.time()
    print('Script finished in {} s'.format(t_end-t_start))

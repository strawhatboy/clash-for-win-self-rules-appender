
import time
t_start = time.time()

import argparse
import sys
import os
import yaml
import watchdog.events
import watchdog.observers

class RuleAppender:
    target_file = ''

    def on_created_func(event):
        print('file created: {}'.format(event.src_path))
        # merge it with ours
        print('Updating...')
        myconf = yaml.load(open('myconf.yml', 'r'), Loader=yaml.CLoader)
        newconf = yaml.load(open(event.src_path, 'r'), Loader=yaml.CLoader)
        newconf['Rule'] = myconf['Rule'] + newconf['Rule']
        with open(RuleAppender.target_file, 'w') as f:
            f.write(yaml.dump(newconf, Dumper=yaml.CDumper))
            f.flush()
            print('Successfully updated custom config file {}'.format(RuleAppender.target_file))

    def main(argvs):
        parser = argparse.ArgumentParser()
        parser.add_argument('--config', help='file to be written, you can locate it by clicking \'Edit in Text Mode\' on your clashR config')
        argv = parser.parse_args(argvs)
        RuleAppender.target_file = argv.config
        filepath = os.path.dirname(argv.config)

        handler = watchdog.events.PatternMatchingEventHandler(patterns='*.yml')
        handler.on_created = RuleAppender.on_created_func

        observer = watchdog.observers.Observer()
        observer.schedule(handler, filepath)
        observer.start()

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


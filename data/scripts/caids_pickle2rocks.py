import argparse
import os
import pickle
import shutil
import tarfile

from rocksdict import Options, Rdict


def main(args):
    options = Options(raw_mode=True)
    db = Rdict(args.rocks_dir, options)

    with open(args.pickle_file, 'rb') as f:
        caids = pickle.load(f)

    for key, value in caids.items():
        db.put(key.encode('utf-8'), value.encode('utf-8'))

    db.close()

    with tarfile.open(args.output_rocks_tar, 'w:gz') as tar:
        tar.add(args.rocks_dir, arcname=os.path.basename(args.rocks_dir))

    if args.delete_rocks:
        shutil.rmtree(args.rocks_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pickle-file', type=str, required=True)
    parser.add_argument('--output-rocks-tar', type=str, required=True)
    parser.add_argument('--rocks-dir', type=str,
                        required=False, default='rocksdict')
    parser.add_argument('--delete-rocks', action='store_true', default=False)
    args = parser.parse_args()
    main(args)

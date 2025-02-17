#!./venv/bin/python3
import asyncio
import logging
from pyndn import Face, Name
from pyndn.security import KeyChain
from src import *
from src.asyncndn import *

DO_PROFILING = False

if DO_PROFILING:
    import cProfile, pstats, io
    from pstats import SortKey
    pr = cProfile.Profile()
    pr.enable()



def main():
    async def face_loop():
        nonlocal face, repo
        while repo.running:
            face.processEvents()
            await asyncio.sleep(0.001)

    config = get_yaml()
    logging.info(config)

    face = Face()
    keychain = KeyChain()
    face.setCommandSigningInfo(keychain, keychain.getDefaultCertificateName())
    # storage = LevelDBStorage(config['db_config']['leveldb']['dir'])
    storage = MongoDBStorage(config['db_config']['mongodb']['db'], config['db_config']['mongodb']['collection'])
    read_handle = ReadHandle(face, keychain, storage)
    write_handle = WriteCommandHandle(face, keychain, storage, read_handle)
    delete_handle = DeleteCommandHandle(face, keychain, storage)
    tcp_bulk_insert_handle = TcpBulkInsertHandle(storage, read_handle,
                                                 config['tcp_bulk_insert']['addr'],
                                                 config['tcp_bulk_insert']['port'])

    repo = Repo(Name(config['repo_config']['repo_name']), face, storage, read_handle, write_handle,
                delete_handle, tcp_bulk_insert_handle)

    repo.listen() # my nfd is broken...

    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(face_loop())
    finally:
        event_loop.close()


if __name__ == "__main__":
    logging.basicConfig(format='[%(asctime)s]%(levelname)s:%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    try:
        main()
    except KeyboardInterrupt:
        pass



if DO_PROFILING:
    pr.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())
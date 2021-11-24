

from multiprocessing import Queue, Process
# import time

# async def worker(name, queue):
#     while True:
#         sleep_for = await queue.get()
#         await asyncio.sleep(sleep_for)
#         queue.task_done()
#         print(f'{name} has slept for {sleep_for:0.2f} seconds')
#
# def wait(sec):
#     print(f'Waiting {sec} seconds')
#     time.sleep(sec)
#     print(f'Done with {sec} sec process')

async def main():
    print('Hello ...')
    await asyncio.sleep(5)
    print('... World!')

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
    # q = Queue()
    # p = Process(target=f, args=(q,5))
    # p.start()
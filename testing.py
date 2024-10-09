# # Open the file in read mode
# def read_tank_info(filename):
#     with open(filename, 'r') as file:
#         # Read all lines from the file
#         lines = file.readlines()
#     height_str = lines[0]
#     write_api = lines[1]
#     height_list = [int(height) for height in height_str.split(',')]
#     write_api_list = [api for api in write_api.split(',')]
#     return height_list, write_api_list

# a, b = read_tank_info('tankheight.txt')
# print(a)
# print(b)

N = 4
empty_lists = [[] for _ in range(N)]
print(empty_lists)


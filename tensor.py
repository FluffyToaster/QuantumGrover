import numpy as np

def double_tensor(a,b):
    return np.tensordot(a, b, axes=0).transpose((0, 2, 1, 3)).reshape((4, 4))

def triple_tensor(a,b,c):
    return np.tensordot(a, np.tensordot(b, c, axes=0).transpose((0, 2, 1, 3)).reshape((4, 4)), axes=0).transpose((0, 2, 1, 3)).reshape((8, 8))

def mult(*args):
    print(args[0].shape, args[1].shape)
    mult_result = np.matmul(args[0], args[1])
    print(mult_result.shape)

    if len(args) == 2:
        return mult_result

    print("recursing {}".format(len(args)))
    recursed_result = mult(mult_result, args[2:])
    print("recursed result {}".format(recursed_result.shape))
    return recursed_result

i = np.matrix([[1,0],
               [0,1]])

x = np.matrix([[0,1],
               [1,0]])

h = np.matrix([[1,1],
               [1,-1]])

toffoli = np.matrix([[1,0,0,0,0,0,0,0],
                     [0,1,0,0,0,0,0,0],
                     [0,0,1,0,0,0,0,0],
                     [0,0,0,1,0,0,0,0],
                     [0,0,0,0,1,0,0,0],
                     [0,0,0,0,0,1,0,0],
                     [0,0,0,0,0,0,0,1],
                     [0,0,0,0,0,0,1,0]])

result = np.matmul(
    triple_tensor(x,x,x),
    np.matmul(
    triple_tensor(i,i,h),
    np.matmul(
    toffoli,
    np.matmul(
    triple_tensor(i,i,h),
    triple_tensor(x,x,x)))))
# triple_tensor(h,h,h))
print(result)


# AAAA = mult(double_tensor(h,h),
#             np.matrix([[1,0,0,0],
#                        [0,-1,0,0],
#                        [0,0,1,0],
#                        [0,0,0,-1]]),
#             double_tensor(h,h))
# print(AAAA)

# print(triple_tensor(x,x,x))
# print(triple_tensor(h,i,i))
# print(toffoli)
# print(triple_tensor(h,i,i))
# print(triple_tensor(x,x,x))

# triple_i = triple_tensor(i,i,i)
# print(mult(triple_i, triple_i))
# print(np.tensordot(i,i,axes=0))
import math

## my first generator
def knudsGenerator():
    yield 1
    yield 2
    i = 3
    while True:
        iPrime = True
        for k in range(3, int(math.sqrt(i) + 1), 2):
            if i % k == 0:
                iPrime = False
                break
        if iPrime:
            yield i
        i = i+2

kg = knudsGenerator()
print next(kg)
print next(kg)
print next(kg)
print next(kg)
print next(kg)
print next(kg)


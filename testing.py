import numpy as np
from sklearn.neighbors import KDTree

rng = np.random.RandomState(0)
X = rng.random_sample((10, 2))
tree = KDTree(X, leaf_size = 2, metric = 'euclidean')              
dist, ind = tree.query(X[:1], k = 2)       
print(X)
print(ind)

print(dist)
import pandas as pd
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("results/k-dist.csv", sep="\t")

pca_cdn_obj = PCA(n_components=10)
pca_cdn = pca_cdn_obj.fit_transform(df[list(df)[2:]].values)



PC_values = np.arange(pca_cdn_obj.n_components_) + 1
plt.plot(PC_values, pca_cdn_obj.explained_variance_ratio_, 'o-', linewidth=2, color='blue')
print(pca_cdn_obj.explained_variance_ratio_)

plt.title('Scree Plot')
plt.xlabel('Principal Component')
plt.ylabel('Variance Explained')
# plt.show()
plt.savefig("results/screeplot.png")


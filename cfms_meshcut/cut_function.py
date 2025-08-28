from enum import Enum
from collections import namedtuple


class cutType(Enum):
    no_cut = 0

    kmeans = 1
    scipy_kmeans2 = 2
    aggler = 3
    DBSCAN = 4
    KMedoids = 5

    bone_pairdist = 10
    bone_kmeans = 11
    bone_KMedoids = 12
    bone_p2bdist = 13

CutOption  = namedtuple('CutOption', 'name type number')

def cutFunction(cut_option : CutOption, V, Fc, Vn, Fn, bonetip1, bonetip2):
	groups = centroids = []
	bPerVertex = True
	Tp 	= cut_option.type.value
	No 	= cut_option.number

	if Tp == cutType.kmeans.value:#raw data
		from trimesh.points import k_means
		(centroids, groups) = k_means( Fc, No)#trimesh.points.k_means
		bPerVertex = True

	elif Tp == cutType.scipy_kmeans2.value:#방법2
		from scipy.cluster.vq import kmeans2
		(centroids, groups) = kmeans2(V, No) #scipy.cluster.vq.kmeans
		bPerVertex = False

	elif Tp == cutType.aggler.value:#bVertex로 해야 됨.
		from sklearn.cluster import AgglomerativeClustering
		import networkx as nx
		from sklearn.neighbors import kneighbors_graph
		agg_clustering = AgglomerativeClustering(n_clusters=No, metric='euclidean', linkage='ward',connectivity=None)
		groups = agg_clustering.fit_predict(V)

	elif Tp == cutType.DBSCAN.value:
		from sklearn.cluster import DBSCAN
		result = DBSCAN(eps=No, min_samples=5).fit(V)
		groups = result.labels_

	elif Tp == cutType.KMedoids.value:#kMedoids
		from sklearn_extra.cluster import KMedoids
		km = KMedoids(n_clusters=No,metric="manhattan", random_state=0, max_iter = 300).fit(V)
		groups, centroids = km.labels_, km.cluster_centers_

	#---------bone-based
	#bone-based methods
	elif Tp == cutType.bone_kmeans.value:
		from sklearn.cluster import KMeans
		result = KMeans(n_clusters= len(bonetip1), init=bonetip1, n_init=1)
		result.fit(V)
		(groups, centroids) = (result.labels_, result.cluster_centers_)

	elif Tp == cutType.bone_KMedoids.value:#왜 안됌?
		from sklearn_extra.cluster import KMedoids
		import numpy as np
		km = KMedoids(n_clusters=len(bonetip1),metric="manhattan", random_state=0, max_iter = 300).fit(V)
		groups, centroids = km.labels_, km.cluster_centers_

	elif Tp == cutType.bone_pairdist.value:#k-Medoids, fixed centroid. 제일 잘 되지만 오른 팔목 그룹 오류.
		#https.value://www.google.com/search?q=python+K-Medoids+for+fixed+centroids&sca_esv=440a43a3eb6979b0&sxsrf=AE3TifOSEHY3wAGCU-YTO-evFzh9k5m_7g%3A1752401570371&ei=ooZzaI61FtDP2roPu7X2yQ0&ved=0ahUKEwiOjuzIzLmOAxXQp1YBHbuaPdkQ4dUDCBA&uact=5&oq=python+K-Medoids+for+fixed+centroids&gs_lp=Egxnd3Mtd2l6LXNlcnAiJHB5dGhvbiBLLU1lZG9pZHMgZm9yIGZpeGVkIGNlbnRyb2lkczIFECEYoAEyBRAhGKABSJ0xUPILWLcvcAF4AJABAZgBlAOgAcImqgEIMi0yMC4wLjG4AQPIAQD4AQGYAhSgAvshwgIKEAAYsAMY1gQYR8ICBRAAGO8FwgIIEAAYogQYiQXCAgYQABgIGB7CAgcQIRigARgKwgIEECEYFZgDAIgGAZAGCpIHBjEuMC4xOaAHgUCyBwQyLTE5uAf2IcIHBDE1LjXIBxI&sclient=gws-wiz-serp
		from sklearn_extra.cluster import KMedoids
		from sklearn.metrics.pairwise import pairwise_distances
		import numpy as np
		distances = pairwise_distances(V, bonetip1)
		groups = np.argmin(distances, axis=1)

	elif Tp == cutType.bone_p2bdist.value:#K-medoids, bone과의 거리 기준.  관절을 따라기간 하지만 일부 그룹이 분리되어 있다.
		#https.value://www.google.com/search?q=scklearn+K-Medoids+user+defined+metric&sca_esv=e770264821b4b2f0&sxsrf=AE3TifOE53hwOVgrtzoV9ShG1IgsR_-Drg%3A1752407766763&ei=1p5zaOmVLsKq0-kP6PaZ-AM&ved=0ahUKEwjp2MHT47mOAxVC1TQHHWh7Bj8Q4dUDCBA&uact=5&oq=scklearn+K-Medoids+user+defined+metric&gs_lp=Egxnd3Mtd2l6LXNlcnAiJnNja2xlYXJuIEstTWVkb2lkcyB1c2VyIGRlZmluZWQgbWV0cmljMgUQABjvBTIIEAAYgAQYogQyCBAAGIAEGKIEMgUQABjvBTIIEAAYgAQYogRIpB9QogdY8RZwAXgBkAEAmAHuAqABoROqAQUyLTkuMbgBA8gBAPgBAZgCBaACswfCAgoQABiwAxjWBBhHwgIKECEYoAEYwwQYCpgDAOIDBRIBMSBAiAYBkAYKkgcFMS4wLjSgB6grsgcDMi00uAevB8IHBTEuMy4xyAcH&sclient=gws-wiz-serp
		import numpy as np
		from sklearn_extra.cluster import KMedoids
		from sklearn.metrics.pairwise import pairwise_distances
		from cfms_meshcut.cut_math import point_to_bone_dist
		point6f 	= np.concatenate((V, Vn), axis=1)
		bone6f 		= np.concatenate((bonetip1, bonetip2), axis=1)
		distances = pairwise_distances(point6f, bone6f, metric=point_to_bone_dist)
		groups 		= np.argmin(distances, axis=1)

	return (groups, bPerVertex)


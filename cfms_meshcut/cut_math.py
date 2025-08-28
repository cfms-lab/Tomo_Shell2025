import numpy as np
import trimesh

ps_white = np.array( [255,255,255])

def normalize(x):
	from sklearn.preprocessing import normalize
	return x / np.linalg.norm(x)

def pt_to_plane_dist(point, plane_point, plane_normal):
    vec = np.subtract(point, plane_point).flatten()
    vec = normalize(vec)
    return np.dot( plane_normal, vec)


def append_bbox(bbox1,bbox2):
	bmin = bbox1[0]
	bmax = bbox1[1]
	bmin = np.min( np.column_stack((bmin,bbox2[0])).T , axis=0)
	bmax = np.max( np.column_stack((bmax,bbox2[1])).T , axis=0)
	return np.column_stack((bmin,bmax)).T

def point_to_bone_dist( point6f, bone6f):
	#https://math.stackexchange.com/questions/322831/determing-the-distance-from-a-line-segment-to-a-point-in-3-space
	q  = np.array(point6f[0:3]) #reference vertex (or triangle center)
	qn = np.array(point6f[3:6]) #vertex normal (or triangle normal)
	p1 = np.array(bone6f[0:3]) #a line end
	p2 = np.array(bone6f[3:6])  #the other end
	u  = np.subtract( p2, p1).flatten()
	v  = np.subtract(  q, p1).flatten()
	u_norm = np.linalg.norm( u)
	uv_dot = np.dot( u, v)
	criteria = uv_dot
	if np.abs(u_norm) > 1e-5:  criteria = uv_dot / (u_norm * u_norm)

	#signed_dist1 = pt_to_plane_dist( p1, q, qn) 오히려 잘 안됨
	#signed_dist2 = pt_to_plane_dist( p2, q, qn)
	#if all([signed_dist1 > 0.001,signed_dist2 > 0.001]): return 1e5

	if criteria > 1.:
		return np.linalg.norm( np.subtract( p2, q))
	elif criteria < 1e-5:
		return np.linalg.norm( np.subtract( p1, q))
	#else:# [0,1] interval
	p = p1 + (uv_dot / u_norm / u_norm) *u
	return np.linalg.norm( np.subtract(  p, q))


def rescale(vertices, max_height):#avatar 키가 max_height가 되도록 self.과 joints를 확대시킨다.
	m_min = np.ones(3) * 1e5
	m_max = np.ones(3) * -1e5
	p_min = np.min( vertices,axis=0)
	p_max = np.max( vertices,axis=0)
	m_min = np.min( np.array([p_min, m_min]), axis=0)
	m_max = np.max( np.array([p_max, m_max]), axis=0)

	vec1 = m_min * -1
	D1 = np.eye(4)
	D1[0:3,3] = m_min * -1

	R = trimesh.transformations.euler_matrix(
		RxRyRz[0],
		RxRyRz[1],
		RxRyRz[2], 'syxz')

	finalM = R @ D1
	finalM[:3, :3] *= max_height# / (m_max[2] - m_min[2])

	new_vtx = np.c_[ vertices, np.ones(len(vertices))]
	new_vtx = np.dot(finalM, new_vtx.T).T
	return new_vtx[:,0:3]


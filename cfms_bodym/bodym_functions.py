import numpy as np
from collections import defaultdict
from recordtype import recordtype
from enum import Enum

import trimesh

GirthSlice 	= recordtype('BodySize', 		'name slice')
FeaturePos 	= recordtype('FeaturePos',	'name pos')
SizeLine		= recordtype('SizeLine',	 	'name points')
CutLine			= recordtype('CutLine',			'name slice')

class BodyPart(Enum):
	Head		 = 0
	Bodice 	 = 1
	LeftArm	 = 2
	RightArm = 3
	LeftLeg	 = 4
	RightLeg = 5
	NotKnown = 6

class LandMark(Enum):
  Name	 = 0
  Part	 = 1
  Up 	 	 = 2
  From 	 = 3
  To   	 = 4
  param	 = 5

class BPVector(Enum):
  #몸 전체 방향 벡터
	Up 				= 0
	Front 		= 1
	Back			= 2
	Right 		= 3
	Left   		= 4

	#로컬 벡터
	Head		 	= 5
	Bodice 	 	= 6
	LeftArm 	= 7
	RightArm 	= 8
	LeftLeg 	= 9
	RightLeg 	= 10

BodyPart_data = [
		[BodyPart.LeftArm,	'BP_LArm',			'mixamorig:LeftArm'],
		[BodyPart.RightArm,	'BP_RARm',			'mixamorig:RightArm'],
		[BodyPart.LeftLeg,	'BP_LLeg',			'mixamorig:LeftLeg'],
		[BodyPart.RightLeg,	'BP_RLeg',			'mixamorig:RightLeg'],
		[BodyPart.Bodice,		'BP_Bodice',		'mixamorig:Spine1'],
		[BodyPart.Head, 		'BP_head',			'mixamorig:HeadTop_End',],# 구분이 가장 쉬운 것을 뒤쪽에 넣는다.
		]


landmarks_data = [
	 ['neck_girth', 			BodyPart.Head,	BPVector.Head, 			'mixamorig:Neck',				'mixamorig:Head', .4]
	,['L_armfit_girth', 	BodyPart.Head,	BPVector.Right, 		'mixamorig:LeftArm', 		'mixamorig:RightArm',	1.0]
	,['R_armfit_girth', 	BodyPart.Head,	BPVector.Right, 		'mixamorig:RightArm', 	'mixamorig:LeftArm',	1.0]

	,['waist_girth', 			BodyPart.Bodice,	BPVector.Up, 			'mixamorig:Spine',			'root', 1.]
	,['breast_girth',			BodyPart.Bodice,	BPVector.Bodice, 	'mixamorig:Spine2', 		'root', 1.0]
	,['low_breast_girth',	BodyPart.Bodice,	BPVector.Bodice, 	'mixamorig:Spine2', 		'mixamorig:Spine1', 0.5]
	,['pelvis_girth',  		BodyPart.Bodice,	BPVector.Bodice, 	'mixamorig:RightUpLeg', 'mixamorig:RightLeg',	0.8]

	,['L_thigh_girth', 	BodyPart.LeftLeg,		BPVector.LeftLeg, 'mixamorig:LeftUpLeg', 	'mixamorig:LeftLeg', 0.4]#잘림
	,['L_knee_girth', 	BodyPart.LeftLeg,		BPVector.LeftLeg, 'mixamorig:LeftLeg', 		'root', 1.0]
	,['L_calf_girth', 	BodyPart.LeftLeg,		BPVector.LeftLeg, 'mixamorig:LeftLeg', 		'mixamorig:LeftFoot', 0.5]
	,['L_ankle_girth',	BodyPart.LeftLeg, 	BPVector.LeftLeg, 'mixamorig:LeftFoot',		'root', 1.0]

	,['R_thigh_girth', 	BodyPart.RightLeg,	BPVector.RightLeg, 'mixamorig:RightUpLeg', 'mixamorig:RightLeg', 0.4]#잘림
	,['R_knee_girth', 	BodyPart.RightLeg,	BPVector.RightLeg, 'mixamorig:RightLeg', 	'root', 1.0]
	,['R_calf_girth', 	BodyPart.RightLeg,	BPVector.RightLeg, 'mixamorig:RightLeg', 	'mixamorig:RightFoot', .5]
	,['R_ankle_girth', 	BodyPart.RightLeg,	BPVector.RightLeg, 'mixamorig:RightFoot',	'root', 1.0]

	,['L_upArm_girth',	BodyPart.LeftArm,		BPVector.LeftArm, 'mixamorig:LeftArm',		'mixamorig:LeftForeArm', .5]
	,['L_elbow_girth', 	BodyPart.LeftArm,		BPVector.LeftArm, 'mixamorig:LeftForeArm','root', 1.0]
	,['L_fArm_girth',		BodyPart.LeftArm,		BPVector.LeftArm, 'mixamorig:LeftForeArm','mixamorig:LeftHand', .5]
	,['L_wrist_girth', 	BodyPart.LeftArm,		BPVector.LeftArm, 'mixamorig:LeftHand', 	'mixamorig:LeftForeArm', 1.1]

	,['R_upArm_girth',	BodyPart.RightArm,	BPVector.RightArm, 'mixamorig:RightArm',		'mixamorig:RightForeArm', .5]
	,['R_elbow_girth',	BodyPart.RightArm,	BPVector.RightArm, 'mixamorig:RightForeArm','root', 1.0]
	,['R_fArm_girth',		BodyPart.RightArm,	BPVector.RightArm, 'mixamorig:RightForeArm','mixamorig:RightHand', .5]
	,['R_wrist_girth',	BodyPart.RightArm,	BPVector.RightArm, 'mixamorig:RightHand', 	'mixamorig:RightForeArm', 1.1]

]

feature_points_data = [
	["L_shoulder", 	'L_armfit_girth',	BPVector.Up],
	["R_shoulder", 	'R_armfit_girth',	BPVector.Up],
	["L_wrist", 		'L_wrist_girth',	BPVector.Back],
	["R_wrist", 		'R_wrist_girth', 	BPVector.Back],
	["L_elbow", 		'L_elbow_girth', 	BPVector.Back],
	["R_elbow", 		'R_elbow_girth', 	BPVector.Back],

	['L_waist',			'waist_girth', 		BPVector.Left],
	['R_waist',			'waist_girth', 		BPVector.Right],
	['F_waist',			'waist_girth', 		BPVector.Front],
	['rear_waist', 	'waist_girth', 		BPVector.Back],#삐뚤함. cutline_bodice 참고.

	['front_neck', 	'neck_girth', 		BPVector.Front],
	['rear_back', 	'neck_girth', 		BPVector.Back],
	['L_side_neck', 'neck_girth', 		BPVector.Left],
	['R_side_neck', 'neck_girth', 		BPVector.Right],

	['L_inner_ankle', 'L_ankle_girth', BPVector.Right],
	['R_inner_ankle', 'R_ankle_girth', BPVector.Left],
	['L_outer_ankle', 'L_ankle_girth', BPVector.Left],
	['R_outer_ankle', 'R_ankle_girth', BPVector.Right],
]

length_data= [
	['L_inseam_line', 	'crotch', 	'L_inner_ankle'],
	['R_inseam_line', 	'crotch', 	'R_inner_ankle'],
	['L_outseam_line', 	'L_waist',	'L_outer_ankle'],
	['R_outseam_line', 	'R_waist',	'R_outer_ankle'],
	['L_shoulder_line', 'L_shoulder', 'L_wrist'],
	['R_shoulder_line', 'R_shoulder', 'R_wrist'],
]


def get( lm, em):
  return lm[em.value]

def get_closest_boundary(slice, origin):
	L = len(slice.entities)
	if L <= 1: return slice

	dist = np.ones( L) * 1e5
	for e_id, entity in enumerate(slice.entities):
		if entity.closed:
			entity_center = np.average(slice.vertices[entity.nodes[:,0]],axis=0)
			dist[e_id] = np.linalg.norm( origin - entity_center )

	min_id = np.argmin( dist)
	new_slice = trimesh.path.Path3D(
			entities = [ slice.entities[min_id] ],
   		vertices = slice.vertices)
	new_slice.remove_unreferenced_vertices()
	return new_slice


#https://stackoverflow.com/questions/76435070/how-do-i-use-python-trimesh-to-get-boundary-vertex-indices
def get_boundaries(mesh, close_paths=True):
	edge_set = set()
	boundary_edges = set()

	for e in map(tuple, mesh.edges_sorted):
			if e not in edge_set:
					edge_set.add(e)
					boundary_edges.add(e)
			elif e in boundary_edges:
					boundary_edges.remove(e)
			else:
					raise RuntimeError(f"The mesh is not a manifold: edge {e} appears more than twice.")

	neighbours = defaultdict(lambda: [])
	for v1, v2 in boundary_edges:
			neighbours[v1].append(v2)
			neighbours[v2].append(v1)

	boundary_paths = []

	while len(boundary_edges) > 0:
			v_previous, v_current = next(iter(boundary_edges))
			boundary_vertices = [v_previous]

			while v_current != boundary_vertices[0]:
					boundary_vertices.append(v_current)

					v1, v2 = neighbours[v_current]
					if v1 != v_previous:
							v_current, v_previous = v1, v_current
					elif v2 != v_previous:
							v_current, v_previous = v2, v_current
					else:
							raise RuntimeError(f"Next vertices to visit ({v1=}, {v2=}) are both equal to {v_previous=}.")
			if close_paths:
					boundary_vertices.append(boundary_vertices[0])

			boundary_paths.append(mesh.vertices[boundary_vertices])
			boundary_edges = set(e for e in boundary_edges if e[0] not in boundary_vertices)

	#choose_closest()함수 재활용을 위해 path3d 형태로 돌려준다.
	entities = []
	vertices = np.empty((0,3))
	nV_sum = 0
	for path in boundary_paths:
		nV = len(path)-1
		vertices = np.append( vertices, np.array(path), axis=0)
		edges = np.arange(nV+1) + nV_sum
		edges[-1] = nV_sum#폐곡선을 만들기 위해 끝점을 한 번 더 넣어준다.
		new_entity = trimesh.path.entities.Line(edges)
		entities.append(new_entity)
		nV_sum += nV
	return trimesh.path.Path3D( vertices=vertices,entities=entities	)


def get_vtx_to_dir(vertices, vec):
	dist = np.dot( np.array(vertices), vec)
	max_id = np.argmax( dist)
	return vertices[max_id]

def get_p2p_dist( pos1, pos2):
	return  np.linalg.norm( np.subtract( pos1, pos2 ))

def get_p2vtx_dist( pos, vtx0):
	dist = np.linalg.norm( np.subtract( np.array(vtx0), pos ), axis=1)
	return dist

def get_non_boundary_vertices(tmesh):
	boundary_edges = tmesh.edges[trimesh.grouping.group_rows(tmesh.edges_sorted, require_count=1)]
	boundary_vertices = np.unique(boundary_edges)
	all_vertices = np.unique(tmesh.faces)
	non_boundary_vertices = np.setdiff1d(all_vertices, boundary_vertices)
	return tmesh.vertices[non_boundary_vertices]


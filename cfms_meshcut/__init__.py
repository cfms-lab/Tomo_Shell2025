import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import trimesh
import numpy as np
import polyscope as ps
from copy import copy

from cut_colors import cutColorSpan, DefaultFilamentColors
from cut_group import CutGroup
from cut_function import cutFunction, cutType
from cut_object import CutObject


class CutManager:
	name = "cuts"
	hfManager = None #Todo: 그냥 trimesh로 대체하기.
	joints = None#이거 필요한가? 그냥 함수 파라미터로 받아도 될 듯.
	ps_raw_group = None #polyscope graph node for raw mesh

	def __init__(self, gltfAvatar,  max_height = None, rotation_angle=None):
		self.hfManager = gltfAvatar.manager
		if self.hfManager.animator: 		self.joints = self.hfManager.animator.joints
		if rotation_angle is not None: 	self.RxRyRz = rotation_angle
		self.tmesh = copy(gltfAvatar.tmesh)

	def choose_group_id_to_move_to(self, group_ids):
		if   group_ids[0] == group_ids[1]:	return group_ids[0]
		elif group_ids[1] == group_ids[2]:	return group_ids[1]
		else:								return group_ids[2]

	def cut_mesh(self, cut_method):
		self.name =  f"{cut_method.name}_cut"

		self.cuts = []
		HF = self.hfManager
		T = self.tmesh
		J = self.joints
		V  = np.array( T.vertices, copy = True)
		Vn = np.array( T.vertex_normals, copy = True)
		F  = np.array( T.faces, copy = True)
		FC = np.array( T.triangles_center, copy = True)
		Fn = np.array( T.face_normals, copy = True)
		B1, B2= HF.get_bone_pos() # parent/child xyz coordinates

		#prepare polyscope graph
		new_ps_id = ps.create_group( f"{self.name}_G")
		colorspan = cutColorSpan(DefaultFilamentColors)
		cutobjects = []
		color_id = 0

		if cut_method.type.value == cutType.no_cut.value:#for no_cut option
			object_name = f"{self.name}_sub_no_cut"
			new_object = CutObject( object_name, T, colorspan, color_id)
			cutobjects.append( new_object) #prepare rendering data
			newcut = CutGroup( self.name, new_ps_id, self.joints, cutobjects )
			self.cuts.append( newcut)
			return newcut

		#Do (K-Means) clustering
		k_groups, bPerVertex = cutFunction(
			cut_method,
			V , FC,
			Vn, Fn,
   		bonetip1   = B1,
			bonetip2   = B2
 			)

		#classify elements w.r.t. "k_groups" ID
		faces_sequences = [[] for _ in range(len(k_groups))]
		if bPerVertex:
			for face_id, face in enumerate(F):#
				vtx = face[0:3] #three triangle vertex IDs
				vtx_groups = k_groups[vtx]
				group_id = self.choose_group_id_to_move_to( vtx_groups)
				faces_sequences[group_id].append( face_id)
		else:#perFace
			for face_id, group_id in enumerate(k_groups):
				faces_sequences[group_id].append( face_id)

		#split mother mesh using trimesh.submesh()
		bSplitFarAway = False#debug
		for f_s_id, f_s in enumerate(faces_sequences):
			if f_s:
				T1 = trimesh.util.submesh( T, [f_s], repair=False, only_watertight=False)[0]

				if bSplitFarAway:
					T1_split = T1.split(only_watertight=False)# 엉뚱하게 떨어져 있는 조각들은 독립시켜 따로 등록한다.
					for t_s in T1_split:
						if len(t_s.vertices) > 3:
							object_name = f"{self.name}_sub{f_s_id:02d}{color_id:02d}"
							new_object = CutObject( object_name, t_s, colorspan, color_id)
							cutobjects.append( new_object) #prepare rendering data
							color_id += 1
				else:
					object_name = f"{self.name}_sub{f_s_id:02d}{color_id:02d}"
					new_object = CutObject( object_name, T1, colorspan, color_id)
					cutobjects.append( new_object) #prepare rendering data
					color_id += 1

		newcut = CutGroup( self.name, new_ps_id, self.joints, cutobjects )
		self.cuts.append( newcut)

		return newcut


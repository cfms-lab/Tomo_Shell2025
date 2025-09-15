import numpy as np
import networkx as nx
from trimesh.curvature import discrete_mean_curvature_measure
from cfms_bodym.bodym_functions import *
import potpourri3d as pp3d


class BodyMeasure:
	def __init__(self, avatar, cut_group):
		self.avatar = avatar
		self.cut_group		= cut_group
		self.BodyPart = [BodyPart.Bodice for _ in range(len(BodyPart))]
		self.girths  = []
		self.features = []
		self.cutlines = []
		self.sizelines  = []

		self.prepare_graph()
		self.prepare_basis_vec()

	def measure(self):
		self.find_girths()
		self.find_feature_points()
		self.find_lengths()

	def prepare_graph(self):
		edges 	= self.avatar.tmesh.edges_unique
		length	= self.avatar.tmesh.edges_unique_length
		self.G = nx.Graph()
		for edge, L in zip(edges, length):
				self.G.add_edge(*edge, length=L)

	def getBPVec(self, vec_name):
		if vec_name == BPVector.Up:
			return self.up
		elif vec_name == BPVector.Right:
			return self.right
		elif vec_name == BPVector.Left:
			return self.right * -1.
		elif vec_name == BPVector.Front:
			return self.front
		elif vec_name == BPVector.Back:
			return self.front * -1.
		elif vec_name == BPVector.Head:
			return self.head
		elif vec_name == BPVector.Bodice:
			return self.bodice
		elif vec_name == BPVector.LeftArm:
			return self.L_arm
		elif vec_name == BPVector.RightArm:
			return self.R_arm
		elif vec_name == BPVector.LeftLeg:
			return self.L_leg
		elif vec_name == BPVector.RightLeg:
			return self.R_leg

	def prepare_basis_vec(self):
		M = self.avatar.manager
		self.right 	= M.get_unit_vec( 'mixamorig:LeftHand',		'mixamorig:RightHand')
		self.up			= M.get_unit_vec( 'mixamorig:Spine', 			'mixamorig:HeadTop_End')
		self.front	=	np.cross( self.up, self.right)

		self.L_arm  = M.get_unit_vec( 'mixamorig:LeftHand',		'mixamorig:LeftForeArm')
		self.R_arm  = M.get_unit_vec( 'mixamorig:RightHand',	'mixamorig:RightForeArm')

		self.L_leg  = M.get_unit_vec( 'mixamorig:LeftFoot',		'mixamorig:LeftLeg')
		self.R_leg  = M.get_unit_vec( 'mixamorig:RightFoot',	'mixamorig:RightLeg')

		self.head   = M.get_unit_vec( 'mixamorig:Neck', 			'mixamorig:Head')
		self.bodice	= M.get_unit_vec( 'mixamorig:Spine',			'mixamorig:Spine2')

		for c_o in self.cut_group.cutobjects:
			c_o.BodyPartID = BodyPart.NotKnown #초기화

		C_O = self.cut_group.cutobjects
		bp_data = BodyPart_data.copy()
		while len(bp_data) > 0:
			bp_id, bp_name, ft_name  = bp_data.pop()
			ft_pos = M.get_bone_pos_by_name(ft_name)
			ft2co_dist = np.ones(len(C_O)) * 1e5
			for id, c_o in enumerate(C_O):
				if c_o.BodyPartID == BodyPart.NotKnown:
					ft2co_dist[id] = get_p2p_dist( ft_pos, c_o.tmesh.centroid)
			nearest_id = np.argmin(ft2co_dist)
			C_O[nearest_id].BodyPartID = bp_id
			C_O[nearest_id].name = bp_name + "__"+C_O[nearest_id].name #for rendering


	def get_girth(self, name):
		for girth in self.girths:
			if girth.name == name:
				return girth.slice

	def get_feature_pos(self, name):
		for ft in self.features:
			if ft.name == name:
				return np.array(ft.pos)

	def set_feature_pos(self, name, new_pos):
		for ft in self.features:
			if ft.name == name:
				ft.pos = new_pos
				return

	def get_nearest_v_id_to_feature(self, vtx0, name):
		pos = self.get_feature_pos( name)
		dist = get_p2vtx_dist( pos, vtx0) #np.linalg.norm( np.subtract( np.array(vtx0),  feature_pos ), axis=1)
		min_id = np.argmin( dist)
		return min_id

	def getBP(self, bp_id):
		for c_o in self.cut_group.cutobjects:
			if c_o.BodyPartID == bp_id:
				return c_o
		return None


	def find_girths(self):
		M = self.avatar.manager
		for lm in landmarks_data:
			c_o = self.getBP( get( lm, LandMark.Part))
			if c_o:
				B0 = M.get_bone_pos_by_name( get( lm, LandMark.From))
				B1 = M.get_bone_pos_by_name( get( lm, LandMark.To))
				t  = get( lm, LandMark.param)
				origin = B0 * t + B1 * (1.- t)
				normal = self.getBPVec( get( lm, LandMark.Up))
				slice	 = c_o.tmesh.section(plane_origin= origin, plane_normal= normal)
				if slice:
					slice  = get_closest_boundary( slice, origin)
					if slice:
						self.girths.append( GirthSlice( get( lm, LandMark.Name), slice))


	def find_feature_points(self):
		self._find_addams_apple()
		self._find_breast_point()
		self._find_crotch_point()

		for ft in feature_points_data:
			girth = self.get_girth(ft[1])
			if girth:
				self.features.append( FeaturePos( ft[0], get_vtx_to_dir( girth.vertices, self.getBPVec(ft[2]))))

		self._adjust_waist_points()


	def _find_neck_slice(self):# 이 방법은 p2bone의 경우 노이즈가 많다.
		M = self.avatar.manager
		#흉곽~목 사이 bone에 투사한 점 중 head에 가까운 걸 찾아서 절단중심점으로 쓴다.
		c_o_bodice 	= self.getBP( BodyPart.Bodice)
		c_o_head 		= self.getBP( BodyPart.Head)
		neck = M.get_bone_pos_by_name( 'mixamorig:Neck')

		neck_cut_line = get_boundaries( c_o_bodice.tmesh, close_paths=True)
		neck_cut_line = get_closest_boundary( neck_cut_line, neck )
		#self.cutlines.append( CutLine("cutline_Neck", neck_cut_line)) #debug

		neck_origin  	= get_vtx_to_dir( neck_cut_line.vertices, self.head * -1.)
		neck_slice 		= c_o_head.tmesh.section(plane_origin = neck_origin, plane_normal= self.head)
		if neck_slice:
			self.girths.append( GirthSlice( "neck_slice", neck_slice))


	def _find_addams_apple(self):#얼굴은 google의 mediapipe 같은 이미지 aI가 더 잘되는듯?
		M = self.avatar.manager
		c_o_head			= self.getBP( BodyPart.Head)
		head 					= M.get_bone_pos_by_name( 'mixamorig:Head')
		head_v_slice	= c_o_head.tmesh.section(plane_origin = head, plane_normal= self.right)
		self.cutlines.append(	CutLine('cutline_Head', head_v_slice))
		self.features.append( FeaturePos( "head_tip",  		get_vtx_to_dir( head_v_slice.vertices, self.up - self.front * 0.1)))
		self.features.append( FeaturePos( "head_rear",  	get_vtx_to_dir( head_v_slice.vertices, self.front * -1.)))
		self.features.append( FeaturePos( "chin_lowest",  get_vtx_to_dir( head_v_slice.vertices, self.front - self.up * 0.5)))


	def _find_breast_point(self):
		from sklearn_extra.cluster import KMedoids
		c_o_bodice 	= self.getBP( BodyPart.Bodice)
		T 					= c_o_bodice.tmesh
		nb_vtx			= get_non_boundary_vertices(T)
		G_C 				= discrete_mean_curvature_measure(T, nb_vtx, radius = .01)
		max_ids			= np.argsort(G_C)
		self.features.append( FeaturePos( f"breast{0}", nb_vtx[max_ids[-1]] ))
		self.features.append( FeaturePos( f"breast{1}", nb_vtx[max_ids[-2]] ))


	def _find_crotch_point(self):
		M = self.avatar.manager
		c_o_bodice			= self.getBP( BodyPart.Bodice)
		spine 					= M.get_bone_pos_by_name( 'mixamorig:Spine')
		self.bodice_v_slice	= c_o_bodice.tmesh.section(plane_origin = spine, plane_normal= self.right)
		self.cutlines.append( CutLine( 'cutline_Bodice', self.bodice_v_slice))
		self.features.append( FeaturePos( "crotch", get_vtx_to_dir( self.bodice_v_slice.vertices, self.bodice * -1.)))

	def _adjust_waist_points(self):#수직 수평 절단선의 교점으로 수정한다.
		vtx 		= self.bodice_v_slice.vertices
		for ft_name in ['F_waist', 'rear_waist']:
			ft_pos 	= self.get_feature_pos( ft_name)
			dist 		= get_p2vtx_dist( ft_pos, vtx)
			min_id 	= np.argmin( dist)
			self.set_feature_pos( ft_name, vtx[min_id])

	def find_lengths(self):
		for d in length_data:
			path_pts = self.shortest_path( d[1],  d[2]) #ToDo: Dijkstra 안 이쁨.
			self.sizelines.append( SizeLine( d[0], path_pts))


	def shortest_path(self, feature1, feature2):#slice는 하나짜리 곡선이라고 가정. 폐곡선이 아닐 수도 있음.
   	# https://github.com/nmwsharp/potpourri3d#mesh-geodesic-paths
		T = self.avatar.tmesh
		V, F = np.array(T.vertices), np.array(T.faces)
		path_solver = pp3d.EdgeFlipGeodesicSolver(V, F) # shares precomputation for repeated solves
		f_id1 = self.get_nearest_v_id_to_feature( V, feature1)
		f_id2 = self.get_nearest_v_id_to_feature( V, feature2)
		path_pts = path_solver.find_geodesic_path(v_start=f_id1, v_end=f_id2)# path_pts is a Vx3 numpy array of points forming the path
		return path_pts

	def add_to(self, renderer):
		for ft in self.features:
			mat4x4 = trimesh.transformations.translation_matrix(ft.pos)
			mark = trimesh.primitives.Sphere( radius = .75, transform = mat4x4)
			renderer.register_surface_mesh(ft.name, mark.vertices, mark.faces, color = ( 1., 0., 0.))

		for girth in self.girths:
			renderer.register_curve_network(girth.name, radius=0.001, color = ( 0., 0., 1.),
					nodes = girth.slice.vertices, edges = girth.slice.vertex_nodes)

		for s_l in self.sizelines:
			renderer.register_curve_network(s_l.name, radius=0.001, color = ( 0.3, 0.3, 0.3),
					nodes = s_l.points, edges = "line")

		for c_l in self.cutlines:
			renderer.register_curve_network( c_l.name, radius=0.001, color = ( 1., 1., 0.),
					nodes =	c_l.slice.vertices, edges = c_l.slice.vertex_nodes)

	def translate_by(self,vec):
		vec = vec

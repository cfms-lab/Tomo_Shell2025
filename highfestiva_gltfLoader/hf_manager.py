import numpy as np

from gltf_loader import load_model
from hf_mesh import hfMesh
from hf_textures import hfTextures
from hf_skin_animator import SkinAnimator

class hfManager():
	def __init__(self, renderer, _fname, max_height):
		self.renderer 	= renderer
		self.filename	= _fname
		self.model 		= load_model(_fname)  #raw mesh (without motion)
		self.textures	= hfTextures(renderer, self.model.teximages)
		self.hfmeshes 	= [] #mesh with motion offset

		self.animator	= SkinAnimator(self.renderer, self.model)
		self.animator.start_animate()

		#debug print
		from cfms_tomo.tomo_io import FStr
		for j in self.animator.joints:
			print(j.parent_name, FStr(j.parent_xyz,3), '-->',  j.name, FStr(j.xyz,3))

	def animate(self, delta_time):
		self.animator.play_animation( delta_time)
		self.animator.init_render( self.model.nodes)

	def rebuild_meshes(self):
		# release previous meshes
		if self.hfmeshes:
			for mesh in self.hfmeshes:	del mesh
			self.hfmeshes.clear()# 굳이 clear할 필요가 있나?
		# build new ones
		if self.animator.skinned_primitives:#텍스쳐 있는 경우
			for m in self.animator.skinned_primitives:
				tex_id = m.material
				meshname = f"{self.model.name}_{tex_id}"
				texname = self.model.teximages[tex_id].name
				tex_data = self.textures.get(texname)
				new_hfMesh = hfMesh(self.renderer, meshname, m, tex_data)
				self.hfmeshes.append( new_hfMesh)
		else:#텍스쳐 없는 경우
			for m_id, m in enumerate(self.model.meshes):
				for p_id, p in enumerate( m.primitives):
					meshname = f"{self.model.name}_{m_id}_{p_id}"
					self.hfmeshes.append(hfMesh(self.renderer, meshname, p, None))

	def get_bone_pos(self):
		child_xyz = [] # coordinates of bone
		parent_xyz = [] #plane normal vector, pointing to the parent direction
		for j in self.animator.joints:
			if len(j.parent_name) > 0:
				child_xyz.append( j.xyz)
				parent_xyz.append( j.parent_xyz)
		child_xyz = np.array(child_xyz)
		parent_xyz = np.array(parent_xyz)
		return parent_xyz, child_xyz

	def add_to(self, renderer, parent_gp=None):
		#show hfMesh
		for mesh in self.hfmeshes:
			ps_mesh = mesh.add_to(renderer)
			if parent_gp: ps_mesh.add_to_group(parent_gp)

		#show joints
		self.animator.add_to(renderer, parent_gp)



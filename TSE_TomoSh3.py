import polyscope
from cfms_bodym.bodym_batchWorks import Batch
from highfestiva_gltfLoader import gltfLoader
from cfms_meshcut.cut_function import cutType, CutOption
from cfms_bodym import BodyMeasure
from cfms_bodym.bodym_functions import BodyPart

avatar = gltfLoader( # (1) GLTF 파일 열기. max_height는 mm단위. SizeKorea '키' 값.
		renderer = polyscope,
		#filename = 'MeshData/masha1_jumpingDown_rest.gltf',	max_height = 1759.94
		#filename = 'MeshData/SK6th_F20_4k_NoFinger.gltf',		max_height = 1650.01,
		filename = 'MeshData/SK6th_F20_10k_NoFinger.gltf',	max_height = 1650.01,
		#filename = 'MeshData/SK6th_M20_4k_NoFinger.gltf',		max_height = 1759.94,
		#filename = 'MeshData/SK6th_M20_87k_NoFinger.gltf',	max_height = 1759.94
		)

batch = Batch( # (2) 메쉬 분할
	avatar = avatar,
	cut_options = [
		#CutOption( 'kmeans/5',			cutType.kmeans, 5),  	#optional
		#CutOption( 'kmedoids/5',		cutType.KMedoids, 5),	#optional
		#CutOption( 'aggler',				cutType.aggler, 5),		#optional
		CutOption( 'bone_pairdist',	cutType.bone_pairdist, 6),#필수. 여기서 Head 가져다 쓴다
		CutOption( 'bone_p2bdist', 	cutType.bone_p2bdist, 6)],#필수. 여기서 나머지 bodypart 갖다 쓴다.
	slicing_option = None # (3D프린터 슬라이싱 옵션. 여기서는 안씀)
	)

body_parts = batch.getBodyParts([
  	['bone_pairdist',	BodyPart.Head],
		['bone_p2bdist',	BodyPart.Bodice],
		['bone_p2bdist',	BodyPart.LeftArm],
		['bone_p2bdist',	BodyPart.RightArm],
		['bone_p2bdist',	BodyPart.LeftLeg],
		['bone_p2bdist',	BodyPart.RightLeg]
	])

bodym			= BodyMeasure( avatar, body_parts) # (4) 인체 계측
bodym.measure()

# (5) 렌더링
avatar.add_to(polyscope)
batch.layout2D() # body들을 겹치지 않게 좌우로 이동시킴
batch.add_to(polyscope)
bodym.add_to(polyscope)
polyscope.show()

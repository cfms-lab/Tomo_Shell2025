import polyscope
from cfms_bodym.WorkManager import WorkManager
from highfestiva_gltfLoader import gltfLoader
from cfms_meshcut.cut_function import cutType, CutOption
from cfms_bodym import BodyMeasure
from cfms_bodym.bodym_functions import BodyPart
from cfms_meshcut.cut_function import StartTimer, EndTimer

time0 = StartTimer("Starting")

avatar = gltfLoader( # (1) GLTF 파일 열기. max_height는 mm단위. SizeKorea '키' 값.
		renderer = polyscope,
		filename = 'MeshData/SK6th_F20_4k_NoFinger.gltf',		max_height = 165.001,
		#filename = 'MeshData/SK6th_F20_10k_NoFinger.gltf',	max_height = 165.001,
		#filename = 'MeshData/SK6th_M20_4k_NoFinger.gltf',		max_height = 175.99,
		#filename = 'MeshData/SK6th_M20_4k_NoFinger_JumpDown.gltf',		max_height = 175.99,
		#filename = 'MeshData/SK6th_M20_87k_NoFinger.gltf',	max_height = 175.99,
		)

manager = WorkManager( # (2) 메쉬 분할
	avatar = avatar,
	cut_options = [
		CutOption( 'kmeans/5',			cutType.kmeans, 5),  				#optional
		CutOption( 'kmedoids/5',		cutType.KMedoids, 5),				#optional
		CutOption( 'aggler5',				cutType.aggler, 5),					#optional
		CutOption( 'bone_pairdist',	cutType.bone_pairdist, 6),	#필수. 여기서 Torso 가져다 쓴다
		CutOption( 'bone_p2bdist', 	cutType.bone_p2bdist, 6)],	#필수. 여기서 6개 bodypart 갖다 쓴다.
	)

body_parts = manager.getBodyParts([ # (3) 계측용으로 아바타의 조각들을 모은다.
  	['bone_pairdist',	BodyPart.Head,			BodyPart.Torso], #'bone_pairdist'의 Head는 이름을 Torso로 구분해서 목/겨드랑이 분리용으로 추가로 가져온다.
		['bone_p2bdist',	BodyPart.Head,			None],
		['bone_p2bdist',	BodyPart.Bodice, 		None],
		['bone_p2bdist',	BodyPart.LeftArm, 	None],
		['bone_p2bdist',	BodyPart.RightArm, 	None],
		['bone_p2bdist',	BodyPart.LeftLeg, 	None],
		['bone_p2bdist',	BodyPart.RightLeg, 	None]
	])

bodym			= BodyMeasure( avatar, body_parts, # (4) 인체 계측
		manager.works[0].bodym#최종 계측일 때는 BodyPart 이름 검사 패스.
  )
bodym.measure()

EndTimer(time0, "Ending")

# (5) 렌더링
avatar.add_to(polyscope)
manager.layout2D() # body들을 겹치지 않게 좌우로 이동시킴
manager.add_to(polyscope)
bodym.add_to(polyscope)
polyscope.show()

import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import urllib
import math
import time

#
# AValue3DSlicerModule
#
class AValue3DSlicerModule(ScriptedLoadableModule):
	"""Uses ScriptedLoadableModule base class,
	available at:https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py """

	def __init__(self, parent):
		ScriptedLoadableModule.__init__(self, parent)
		self.parent.title = "A-Value Measurement"
		self.parent.categories = ["Otolaryngology"]
		self.parent.dependencies = []
		self.parent.contributors = ["John Eniolu (Auditory Biophyiscs Lab)"]
		self.parent.helpText = """
		This is a scripted loadable module.
		It measures the A-value, used to estimate Cochlear Duct Length."""
		self.parent.helpText += self.getDefaultModuleDocumentationLink()
		self.parent.acknowledgementText = """This process was developed at
		Western University(Ontario, CA) in the Auditory Biophyiscs Lab """

#
# AValue3DSlicerModuleWidget
#
class AValue3DSlicerModuleWidget(ScriptedLoadableModuleWidget):
	"""Uses ScriptedLoadableModuleWidget base class,
	available at:https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py"""

	def setup(self):
		ScriptedLoadableModuleWidget.setup(self)

		# Instantiate and connect widgets ...

		#
		# PARAMETER AREA
		#
		parametersCollapsibleButton = ctk.ctkCollapsibleButton()
		parametersCollapsibleButton.text = "Procedure"
		self.layout.addWidget(parametersCollapsibleButton)

		# Layout within the input collapsible button
		parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
		#
		# atlas selection checkbox
		#
		self.leftAtlas = qt.QCheckBox(" Left Ear ")
		self.leftAtlas.checked = False
		self.leftAtlas.setToolTip("If checked left ear atlas is loaded and used for registration")

		self.rightAtlas = qt.QCheckBox(" Right Ear ")
		self.rightAtlas.checked = False
		self.rightAtlas.setToolTip("If checked right ear atlas is loaded and used for registration")

		earSelector = qt.QHBoxLayout()
		earSelector.addWidget(self.leftAtlas)
		earSelector.addWidget(self.rightAtlas)
		parametersFormLayout.addRow("Atlas Selection: ", earSelector)

		#
		#Load Atlas Button
		#
		self.loadAtlasButton = qt.QPushButton("Load Atlas")
		self.loadAtlasButton.toolTip = "Load Atlas"
		self.loadAtlasButton.enabled = False
		parametersFormLayout.addRow(self.loadAtlasButton)

		#
		# input volume selector
		#
		self.inputSelector = slicer.qMRMLNodeComboBox()
		self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
		self.inputSelector.selectNodeUponCreation = True
		self.inputSelector.addEnabled = False
		self.inputSelector.removeEnabled = False
		self.inputSelector.noneEnabled = True
		self.inputSelector.showHidden = False
		self.inputSelector.showChildNodeTypes = False
		self.inputSelector.setMRMLScene( slicer.mrmlScene )
		self.inputSelector.setToolTip( "select input image." )
		parametersFormLayout.addRow("Input Volume: ", self.inputSelector)


		#
		# Fiduical buttons
		#
		self.OWButton		 	= qt.QPushButton("Oval Window")
		self.OWButton.toolTip 	= "Place Oval Window Fiduical"
		self.OWButton.enabled	= False

		self.CNButton			= qt.QPushButton('Cochlear Nerve')
		self.CNButton.toolTip 	= "Place Cochlear Nerve Fiduical"
		self.CNButton.enabled	= False

		self.AButton		 	= qt.QPushButton("Apex")
		self.AButton.toolTip 	= "Place Apex Fiduical"
		self.AButton.enabled	= False

		self.RWButton			= qt.QPushButton('Round Window')
		self.RWButton.toolTip 	= "Place Round Window Fiduical"
		self.RWButton.enabled	= False

		fiduicalPlacement = qt.QHBoxLayout()
		fiduicalPlacement.addWidget(self.OWButton)
		fiduicalPlacement.addWidget(self.CNButton)
		fiduicalPlacement.addWidget(self.AButton)
		fiduicalPlacement.addWidget(self.RWButton)
		parametersFormLayout.addRow("Fiduical Placement: ", fiduicalPlacement)

		#
		#Align Button - for initial rigid alignment of images
		#
		self.alignButton 	= qt.QPushButton("Align Volume")
		self.alignButton.toolTip = "Orient input volume to spatial region of Atlas"
		self.alignButton.enabled = False

		# imageAlignment = qt.QHBoxLayout()
		# imageAlignment.addWidget(self.fidButton)
		# imageAlignment.addWidget(self.alignButton)
		parametersFormLayout.addRow(self.alignButton)


		#
		# Define & Crop Volume Button
		#
		self.defineCropButton 			= qt.QPushButton("Define ROI")
		self.defineCropButton.toolTip 	= "Select ROI from atlas image"
		self.defineCropButton.enabled	= False

		self.cropButton					= qt.QPushButton("Crop!")
		self.cropButton.toolTip			= "Crop Image"
		self.cropButton.enabled			= False

		imageCropping = qt.QHBoxLayout()
		imageCropping.addWidget(self.defineCropButton)
		imageCropping.addWidget(self.cropButton)
		parametersFormLayout.addRow("Select & Crop Region of Interest: ", imageCropping)

		#
		# output volume selector
		#
		self.outputSelector = slicer.qMRMLNodeComboBox()
		self.outputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
		self.outputSelector.selectNodeUponCreation = True
		self.outputSelector.addEnabled = True
		self.outputSelector.renameEnabled - True
		self.outputSelector.removeEnabled = True
		self.outputSelector.noneEnabled = True
		self.outputSelector.showHidden = False
		self.outputSelector.showChildNodeTypes = False
		self.outputSelector.setMRMLScene( slicer.mrmlScene )
		self.outputSelector.setToolTip( "select output volume " )
		parametersFormLayout.addRow("Output Atlas Volume: ", self.outputSelector)

		#
		#Output Transform
		#
		self.outputTransformSelector = slicer.qMRMLNodeComboBox()
		self.outputTransformSelector.nodeTypes = ["vtkMRMLBSplineTransformNode"]
		self.outputTransformSelector.addNode()
		self.outputTransformSelector.selectNodeUponCreation = True
		self.outputTransformSelector.addEnabled = True
		self.outputTransformSelector.renameEnabled = True
		self.outputTransformSelector.removeEnabled = True
		self.outputTransformSelector.noneEnabled = True
		self.outputTransformSelector.setMRMLScene( slicer.mrmlScene )
		self.outputTransformSelector.setToolTip( "output transform " )
		parametersFormLayout.addRow("Output BSpline Transform: ", self.outputTransformSelector)

		#
		# Calculate A-Value Button
		#
		self.applyButton = qt.QPushButton("Calculate A-Value")
		self.applyButton.toolTip = "Run the algorithm."
		self.applyButton.enabled = False
		parametersFormLayout.addRow(self.applyButton)

		# connections
		self.leftAtlas.connect('toggled(bool)', self.onLeftEarSelection)
		self.rightAtlas.connect('toggled(bool)', self.onRightEarSelection)
		self.loadAtlasButton.connect('clicked(bool)', self.onLoadAtlasButton)
		self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
		self.OWButton.connect('clicked(bool)', self.onOWButton)
		self.CNButton.connect('clicked(bool)', self.onCNButton)
		self.AButton.connect('clicked(bool)', self.onAButton)
		self.RWButton.connect('clicked(bool)', self.onRWButton)
		self.alignButton.connect('clicked(bool)', self.onAlignButton)
		self.defineCropButton.connect('clicked(bool)', self.onDefineCropButton)
		self.cropButton.connect('clicked(bool)', self.onCropButton)
		self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
		self.outputTransformSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
		self.applyButton.connect('clicked(bool)', self.onApplyButton)

		# Add vertical spacer
		self.layout.addStretch(1)

		# Refresh Apply button state
		self.onSelect()

		# Refresh Ear Selection checkboxes state
		#self.AtlasLoaded = False
		self.onLeftEarSelection()
		self.onRightEarSelection()

		#initialize placed landmark node & respective transform node
		#self.placedLandmarkNode = slicer.vtkMRMLMarkupsFiducialNode()
		#self.LandmarkTrans 		= slicer.vtkMRMLTransformNode()

	def onSelect(self):

		# update status of apply Button
		self.OWButton.enabled = self.inputSelector.currentNode()
									#and self.AtlasLoaded
		self.applyButton.enabled = self.inputSelector.currentNode() \
									and self.outputSelector.currentNode() \
									and self.outputTransformSelector.currentNode()

	def onLeftEarSelection(self):
		if self.leftAtlas.isChecked() == True:
			self.rightAtlas.setChecked(False)
			self.loadAtlasButton.enabled = True

	def onRightEarSelection(self):
		if self.rightAtlas.isChecked() == True:
			self.leftAtlas.setChecked(False)
			self.loadAtlasButton.enabled = True

	def onLoadAtlasButton(self):
		logic = AValue3DSlicerModuleLogic()

		#Check atlas selection
		if(self.rightAtlas.isChecked()):
			self.atlasSelection = "right"
		elif(self.leftAtlas.isChecked()):
			self.atlasSelection = "left"
		else:
			self.atlasSelection = "none"

		self.AtlasLoaded, self.atlasVolume, self.atlasFid = logic.runAtlasLoad(self.atlasSelection)
		self.atlasVolume.SetDisplayVisibility(1) #Make atlas visible

		# #Display Atlas in 3D View
		# sliceWidgetR 	= slicer.app.layoutManager().sliceWidget('Red')
		# sliceWidgetY 	= slicer.app.layoutManager().sliceWidget('Yellow')
		# sliceWidgetG 	= slicer.app.layoutManager().sliceWidget('Green')
		# sliceLogicR = sliceWidgetR.sliceLogic()
		# sliceLogicY = sliceWidgetY.sliceLogic()
		# sliceLogicG = sliceWidgetG.sliceLogic()
		# sliceNodeR = sliceLogicR.GetSliceNode()
		# sliceNodeY = sliceLogicY.GetSliceNode()
		# sliceNodeG = sliceLogicG.GetSliceNode()
		# sliceNodeR.SetSliceVisible(True)
		# sliceNodeY.SetSliceVisible(True)
		# sliceNodeG.SetSliceVisible(True)


	def onOWButton(self):

		#Setup Fiduical placement
		self.placedLandmarkNode = slicer.vtkMRMLMarkupsFiducialNode()
		slicer.mrmlScene.AddNode(self.placedLandmarkNode)
		#Fiduical Placement Widget
		self.fiducialWidget = slicer.qSlicerMarkupsPlaceWidget()
		self.fiducialWidget.buttonsVisible = False
		self.fiducialWidget.placeButton().show()
		self.fiducialWidget.setMRMLScene(slicer.mrmlScene)
		self.fiducialWidget.setCurrentNode(self.placedLandmarkNode)
		self.fiducialWidget.placeMultipleMarkups = slicer.qSlicerMarkupsPlaceWidget.ForcePlaceSingleMarkup

		#Delay to ensure Widget Appears & provide user with info
		slicer.util.infoDisplay("Place the following fiducial:\n\n" +
			 					"Oval Window\n\n" +
								"Press okay when ready to begin" )

		#Enable fiducial placement
		self.fiducialWidget.setPlaceModeEnabled(True)
		#Enable Cochlear Nevre button
		self.OWButton.enabled = False
		self.CNButton.enabled = True


	def onCNButton(self):

		#Delay to ensure Widget Appears & provide user with info
		slicer.util.infoDisplay("Place the following fiducial:\n\n" +
			 					"Cochlear Nerve\n\n" +
								"Press okay when ready to begin" )

		#Enable fiducial placement
		self.fiducialWidget.setPlaceModeEnabled(True)
		#Enable Apex button
		self.CNButton.enabled = False
		self.AButton.enabled = True

	def onAButton(self):

		#Delay to ensure Widget Appears & provide user with info
		slicer.util.infoDisplay("Place the following fiducial:\n\n" +
			 					"Apex\n\n" +
								"Press okay when ready to begin" )

		#Enable fiducial placement
		self.fiducialWidget.setPlaceModeEnabled(True)
		#Enable Round Window button
		self.AButton.enabled = False
		self.RWButton.enabled = True

	def onRWButton(self):

		#Delay to ensure Widget Appears & provide user with info
		slicer.util.infoDisplay("Place the following fiducial:\n\n" +
			 					"Round Window\n\n" +
								"Press okay when ready to begin" )

		#Enable fiducial placement
		self.fiducialWidget.setPlaceModeEnabled(True)
		#Enable alignment button
		self.RWButton.enabled = False
		self.alignButton.enabled = True

	def onAlignButton(self):

		self.RWButton.enabled = False
		#Create Landmark transform placeholder
		self.LandmarkTrans = slicer.vtkMRMLTransformNode()
		slicer.mrmlScene.AddNode(self.LandmarkTrans)

		logic = AValue3DSlicerModuleLogic()

		#Run fiducial registration
		if(self.placedLandmarkNode.GetNumberOfFiducials() == 4):
			logic.runFiducialRegistration(self.rightAtlas.isChecked(), self.LandmarkTrans, self.placedLandmarkNode)
		else:
			slicer.util.infoDisplay("4 Fiducials required for registration") #TODO - add appropriate information to help user!

		#Apply Landmark transform on Atlas Volume then Harden
		self.atlasVolume.SetAndObserveTransformNodeID(self.LandmarkTrans.GetID())
		slicer.vtkSlicerTransformLogic().hardenTransform(self.atlasVolume)
		#Apply Landmark transform on Fiduicals then Harden
		self.atlasFid.SetAndObserveTransformNodeID(self.LandmarkTrans.GetID())
		slicer.vtkSlicerTransformLogic().hardenTransform(self.atlasFid)

		#Set Atlas to foreground in Slice Views
		applicationLogic 	= slicer.app.applicationLogic()
		selectionNode 		= applicationLogic.GetSelectionNode()
		selectionNode.SetSecondaryVolumeID(self.atlasVolume.GetID())
		applicationLogic.PropagateForegroundVolumeSelection(0)

		#set overlap of foreground & background in slice view
		sliceLayout = slicer.app.layoutManager()
		sliceLogicR = sliceLayout.sliceWidget('Red').sliceLogic()
		compositeNodeR = sliceLogicR.GetSliceCompositeNode()
		compositeNodeR.SetForegroundOpacity(0.5)
		sliceLogicY = sliceLayout.sliceWidget('Yellow').sliceLogic()
		compositeNodeY = sliceLogicY.GetSliceCompositeNode()
		compositeNodeY.SetForegroundOpacity(0.5)
		sliceLogicG = sliceLayout.sliceWidget('Green').sliceLogic()
		compositeNodeG = sliceLogicG.GetSliceCompositeNode()
		compositeNodeG.SetForegroundOpacity(0.5)

		self.defineCropButton.enabled	= True # enabled next step "Defining Crop region of interest"
		self.placedLandmarkNode.SetDisplayVisibility(0) #turn off display of placed landmarks -TODO - Is this needed


	def onDefineCropButton(self):

		slicer.app.layoutManager().setLayout(1) #Set to appropriate view (conventional)

		#Define Cropped Volume Parameters
		self.cropVolumeNode = slicer.vtkMRMLCropVolumeParametersNode()
		self.cropVolumeNode.SetScene(slicer.mrmlScene)
		self.cropVolumeNode.SetName('Crop_volume_Node')
		self.cropVolumeNode.SetInputVolumeNodeID(self.atlasVolume.GetID())
		self.cropVolumeNode.VoxelBasedOn()
		logging.info(self.cropVolumeNode.GetVoxelBased())
		slicer.mrmlScene.AddNode(self.cropVolumeNode)


		#Fit ROI to input Volume and initialize in scene
		logic = AValue3DSlicerModuleLogic()
		self.atlasROI 		= slicer.vtkMRMLAnnotationROINode()
		self.atlasROI.Initialize(slicer.mrmlScene)
		self.cropVolumeNode.SetROINodeID(self.atlasROI.GetID())
		self.atlasROI	= logic.runDefineCropROI(self.cropVolumeNode)


		#Instruct user on ROI placement
		slicer.util.infoDisplay("NOTE: Ensure Region of Interest (ROI) encloses atlas in the:"+
								"\n\nAxial (Red)\nSagittal(Yellow)\nCoronal(Green)\n\n"+
		 						"Press okay to continue" )

		self.cropButton.enabled = True

	def onCropButton(self):
		logic = AValue3DSlicerModuleLogic()

		#Crop Image
		self.cropVolume = logic.runCropVolume(	self.atlasROI,
												self.inputSelector.currentNode() )

	def onApplyButton(self):

		#Instantiate logic class
		logic = AValue3DSlicerModuleLogic()

		#Run module logic
		# logic.run(	self.inputSelector.currentNode(), self.outputSelector.currentNode(),
		# 			self.atlasVolume, self.LandmarkTrans,
		# 			self.outputTransformSelector.currentNode(), self.atlasFid )
		logic.run(	self.cropVolume, self.outputSelector.currentNode(),
					self.atlasVolume, self.LandmarkTrans,
					self.outputTransformSelector.currentNode(), self.atlasFid )
	def cleanup(self):
		pass

#
# AValue3DSlicerModuleLogic
#
class AValue3DSlicerModuleLogic(ScriptedLoadableModuleLogic):

	"""This class should implement all the actual
	computation done by your module.  The interface
	should be such that other python code can import
	this class and make use of the functionality without
	requiring an instance of the Widget.
	Uses ScriptedLoadableModuleLogic base class, available at:
	https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
	"""
	#Check input data is provided
	def hasImageData(self,volumeNode):
		"""This is an example logic method that
		returns true if the passed in volume
		node has valid image data
		"""
		if not volumeNode:
	  		logging.debug('hasImageData failed: no volume node')
	  		return False
		if volumeNode.GetImageData() is None:
			logging.debug('hasImageData failed: no image data in volume node')
			return False
		return True

	#Check valid input is provided by user
	def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
		"""Validates if the output is not the same as input
		"""
		if not inputVolumeNode:
			logging.debug('isValidInputOutputData failed: no input volume node defined')
			return False
		if not outputVolumeNode:
			logging.debug('isValidInputOutputData failed: no output volume node defined')
			return False
		if inputVolumeNode.GetID()==outputVolumeNode.GetID():
			logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
			return False
		return True

	#load Atlas and corresponding A-Value Fiducials
	#TODO -Change file location to server location
	def loadAtlasNodeAndFiducials(self, isRight,
									atlasLocationR 		= '/Users/JohnEniolu/Documents/AValueModuleData/initialAtlasR.nrrd' ,
									fiducialLocationR 	= '/Users/JohnEniolu/Documents/AValueModuleData/Atlas_AValue_F.fcsv',
									atlasLocationL 		= '/Users/JohnEniolu/Documents/AValueModuleData/initialAtlasL.nrrd' ,
									fiducialLocationL	= '/Users/JohnEniolu/Documents/AValueModuleData/Atlas_AValue_MF.fcsv'):

		#TODO -Specify location of required data on server
		#atlasLocationR 	= urllib.urlretrieve('<...Insert Server Location of Right Atlas...>',
		#										 'initialAtlasR.nrrd')
		#fiducialLocationR 	= urllib.urlretrieve('<...Insert Server Location of right A-Value...>',
		#										 'Atlas_AValue_F.fcsv')
		#atlasLocationL 	= urllib.urlretrieve('<...Insert Server Location of left Atlas...>',
		#										 'initialAtlasL.nrrd')
		#fiducialLocationL	= urllib.urlretrieve('<...Insert Server Location of left A-Value...>',
		#										 'Atlas_AValue_MF.fcsv')

		#create atlasnode

		if isRight:
			atlasNode = slicer.util.loadVolume(atlasLocationR, returnNode=True)
			atlasFiducial = slicer.util.loadMarkupsFiducialList(fiducialLocationR, returnNode=True)
			logging.info('Loaded right ear atlas')
		else:
			atlasNode = slicer.util.loadVolume(atlasLocationL, returnNode=True)
			atlasFiducial = slicer.util.loadMarkupsFiducialList(fiducialLocationL, returnNode=True)
			logging.info('Loaded left ear atlas')
		return atlasNode, atlasFiducial

	#TODO: Change file location to server location
	def loadAtlasLandmark(	self, isRight,
	 						landmarkLocationR = '/Users/JohnEniolu/Documents/AValueModuleData/initialLandmarkREG_R.fcsv',
							landmarkLocationL = '/Users/JohnEniolu/Documents/AValueModuleData/initialLandmarkREG_L.fcsv'):
		#Load fiducial landmark for initial atlas landmark registration


		#TODO- Specify location of required data on server
		#landmarklLocationR 	= urllib.urlretrieve('<...Insert Server Location of right landmarks...>',
		#										 'initialLandmarkREG_R.fcsv')
		#landmarkLocationL		= urllib.urlretrieve('<...Insert Server Location of left landmarks...>',
		#										 'initialLandmarkREG_L.fcsv')

		if isRight:
			landmarkFid = slicer.util.loadMarkupsFiducialList(landmarkLocationR, returnNode=True)
		else:
			landmarkFid = slicer.util.loadMarkupsFiducialList(landmarkLocationL, returnNode=True)
		logging.info('loading landmarks')
		return landmarkFid[1]#Return fiducial only

	def printStatus(self):
		print('Fiduical placed!!')
		return True

	def runAtlasLoad(self, atlasSelection):

		#TODO - Make A-Value fiducials not visible in GUI

		#check atlas selection then retrive atlas
		if(atlasSelection != 'None'):
			if atlasSelection == 'right':
				self.loadedAtlas, self.loadFid 	= self.loadAtlasNodeAndFiducials(True) #Returns tuple
				self.atlasVolume  				= self.loadedAtlas[1] #Retrieve atlas Volume from tuple
				self.atlasFiducial 				= self.loadFid[1]
				self.atlasFiducial.SetDisplayVisibility(0) #do not display atlas fiducials
				return True, self.atlasVolume, self.atlasFiducial
			elif atlasSelection == 'left':
				self.loadedAtlas, self.loadFid	= self.loadAtlasNodeAndFiducials(False) #False implies not right i.e. left
				self.atlasVolume				= self.loadedAtlas[1]
				self.atlasFiducial				= self.loadFid[1]
				self.atlasFiducial.SetDisplayVisibility(0) #do not display atlas fiducials
				return True, self.atlasVolume, self.atlasFiducial
			else:
				slicer.util.errorDisplay('Atlas not selected. Choose right or left ear atlas')
				return False

	def runFiducialRegistration(self, isRight, rigTrans, placedLandmarkNode ):

		#retrive fixed landmarks
		movingLandmarkNode = self.loadAtlasLandmark(isRight)

		#Setup and Run Landmark Registration
		cliParamsFidReg = {	'fixedLandmarks'	: placedLandmarkNode.GetID(),
						   	'movingLandmarks' 	: movingLandmarkNode.GetID(),
							'transformType' 	: 'Rigid',
							'saveTransform' 	: rigTrans.GetID() }

		cliRigTrans = slicer.cli.run(slicer.modules.fiducialregistration, None,
									  cliParamsFidReg, wait_for_completion=True )

		movingLandmarkNode.SetDisplayVisibility(0) #turn off display for moving landmarks

		#return cliRigTrans


	def runDefineCropROI(self, cropParam):

		vol 		= slicer.mrmlScene.GetNodeByID(cropParam.GetInputVolumeNodeID()	)

		volBounds	= [0,0,0,0,0,0]
		vol.GetRASBounds(volBounds)
		logging.info(volBounds)

		#Find Dimensions of Image
		volDim		= [  (volBounds[1]-volBounds[0]),
						 (volBounds[3]-volBounds[2]),
						 (volBounds[5]-volBounds[4])   ]
		roi			= slicer.mrmlScene.GetNodeByID(cropParam.GetROINodeID())

		#Find Center of Image
		volCenter 	= [  ((volBounds[0]+volBounds[1])/2),
						 ((volBounds[2]+volBounds[3])/2),
						 ((volBounds[4]+volBounds[5])/2)   ]

		roi.SetXYZ(volCenter)
		roi.SetRadiusXYZ(volDim[0]/2, volDim[1]/2, volDim[2]/2 )
		return roi


	def runCropVolume(self, roi, volume):

		#slicer.mrmlScene.AddNode(cropParam)
		#TODO - Crop volume
		cropParamNode = slicer.vtkMRMLCropVolumeParametersNode()
		cropParamNode.SetScene(slicer.mrmlScene)
		cropParamNode.SetName('Crop_volume_Node1')

		#Set volume and ROI required for cropping
		cropParamNode.SetInputVolumeNodeID(volume.GetID())
		cropParamNode.SetROINodeID(roi.GetID())
		cropParamNode.VoxelBasedOff()
		logging.info(cropParamNode.GetVoxelBased())
		slicer.mrmlScene.AddNode(cropParamNode)

		#Apply Cropping
		cropVolumeLogic = slicer.modules.cropvolume.logic()
		cropVolumeLogic.Apply(cropParamNode)
		cropVol = slicer.mrmlScene.GetNodeByID(cropParamNode.GetOutputVolumeNodeID())

		return cropVol

	#Automated A-value implementation
	def run(self, inputVolume, outputVolume, atlasVolume, initialTrans, outputTrans, atlasFid):
		"""
		Run the actual algorithm
		"""
		#check appropriate volume is selected
		if not self.isValidInputOutputData(inputVolume, outputVolume):
			slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
			return False

		logging.info('.....Printing Initial Transform....')
		logging.info(initialTrans)

		#Create intermediate linear transform node
		self.linearTrans = slicer.vtkMRMLTransformNode()
		slicer.mrmlScene.AddNode(self.linearTrans)

		#Set parameters and run affine registration Step 1
		cliParamsAffine = { 'fixedVolume' 		: inputVolume.GetID(),
							'movingVolume'		: atlasVolume.GetID(),
							'linearTransform' 	: self.linearTrans.GetID() }
		cliParamsAffine.update({'samplingPercentage'	: 1,
								'initialTransformMode' 	: 'off',
								'transformType'			: 'Affine'})
		cliParamsAffine.update({'numberOfIterations' 	: 3000,
								'minimumStepLength'		: 0.00001,
								'maximumStepLength'		: 0.05})
		cliAffineTransREG = slicer.cli.run(slicer.modules.brainsfit, None, cliParamsAffine, wait_for_completion=True)

		logging.info('....Printing Affine Transform....')
		logging.info(self.linearTrans)

		#Apply linear transform on Atlas Volume
		#atlasVolume.SetAndObserveTransformNodeID(linearTrans.GetID())
		#slicer.vtkSlicerTransformLogic().hardenTransform(atlasVolume)

		# Set parameters and run BSpline registration Step 2
		cliParams = {	'fixedVolume'		: inputVolume.GetID(),
		 				'movingVolume'		: atlasVolume.GetID(),
						'bsplineTransform' 	: outputTrans.GetID() }
		cliParams.update({	'samplingPercentage': 1,
		 					'initialTransform' 	: self.linearTrans.GetID() })
		cliParams.update({	'transformType'	: 'BSpline',
							'splineGridSize': '3,3,3'})
		cliParams.update({	'numberOfIterations' 	: 3000,
		 					'minimumStepLength'		: 0.00001,
							'maximumStepLength'		: 0.05})
		cliParams.update({'costMetric' : 'NC' })
		cliBSplineREG = slicer.cli.run(slicer.modules.brainsfit, None, cliParams, wait_for_completion=True)

		logging.info('....Printing BSpline Transform....')
		logging.info(outputTrans)

		#Apply BSpline transform on A-Value Fiducials
		atlasFid.SetAndObserveTransformNodeID(outputTrans.GetID())
		slicer.vtkSlicerTransformLogic().hardenTransform(atlasFid)

		#Calculate New A-Value
		numOfFids = atlasFid.GetNumberOfFiducials()
		fidXYZ_RW = [0,0,0] #Round Window placeholder
		fidXYZ_LW = [0,0,0] #Lateral Wall placeholder
		print numOfFids
		for index in range(numOfFids):
			if index == 0:
				atlasFid.GetNthFiducialPosition(index, fidXYZ_RW)
				print fidXYZ_RW
			else:
				atlasFid.GetNthFiducialPosition(index, fidXYZ_LW)
				print fidXYZ_LW

		newAValue = math.sqrt(	((fidXYZ_RW[0] - fidXYZ_LW[0])**2) + \
								((fidXYZ_RW[1] - fidXYZ_LW[1])**2) + \
								((fidXYZ_LW[2] - fidXYZ_RW[2])**2)		)


		#Calculating CDL Estimates
		AlexiadesCDLoc 	= 4.16 * newAValue - 4 		#CDL estimate from Alexiades et al. (2015)
		KochCDLoc 		= 4.16 * newAValue - 5.05	#CDL estimate from Koch et al. (2017)
		KochCDLlw		= 3.86 * newAValue + 4.99	#CDL estimtae from Koch et al. (2017)

		#Display Patient ID and Estimated A Valuee
		outputDisp = "Patient ID:\n" + inputVolume.GetName() + \
					"\n\nEstimated A Value:\n" + format(newAValue, '0.1f') + 'mm\n\n' + \
					"Estimated CDL Values\n" + "CDL(oc)-1: " + format(AlexiadesCDLoc, '0.1f') + 'mm\n' + \
					"CDL(oc)-2: " + format(KochCDLoc, '0.1f') + "mm\n" + \
					"CDL(lw)-1: " + format(KochCDLlw, '0.1f') + "mm\n"

		slicer.util.infoDisplay(outputDisp)

		logging.info('Processing completed')

		return True


class AValue3DSlicerModuleTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
	""" Do whatever is needed to reset the state - typically a scene clear will be enough.
	"""
	slicer.mrmlScene.Clear(0)

  def runTest(self):
	"""Run as few or as many tests as needed here.
	"""
	self.setUp()
	self.test_AValue3DSlicerModule1()

  def test_AValue3DSlicerModule1(self):
	""" Ideally you should have several levels of tests.  At the lowest level
	tests should exercise the functionality of the logic with different inputs
	(both valid and invalid).  At higher levels your tests should emulate the
	way the user would interact with your code and confirm that it still works
	the way you intended.
	One of the most important features of the tests is that it should alert other
	developers when their changes will have an impact on the behavior of your
	module.  For example, if a developer removes a feature that you depend on,
	your test should break so they know that the feature is needed.
	"""

	self.delayDisplay("Starting the test")
	#
	# first, get some data
	#
	import urllib
	downloads = (
		('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
		)

	for url,name,loader in downloads:
	  filePath = slicer.app.temporaryPath + '/' + name
	  if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
		logging.info('Requesting download %s from %s...\n' % (name, url))
		urllib.urlretrieve(url, filePath)
	  if loader:
		logging.info('Loading %s...' % (name,))
		loader(filePath)
	self.delayDisplay('Finished with download and loading')

	volumeNode = slicer.util.getNode(pattern="FA")
	logic = AValue3DSlicerModuleLogic()
	self.assertIsNotNone( logic.hasImageData(volumeNode) )
	self.delayDisplay('Test passed!')

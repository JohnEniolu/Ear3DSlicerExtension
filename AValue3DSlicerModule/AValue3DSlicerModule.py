import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
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
		self.parent.title = "AValue3DSlicerModule" # TODO make this more human readable by adding spaces
		self.parent.categories = ["Examples"]
		self.parent.dependencies = []
		self.parent.contributors = ["John Eniolu (HML & SKA Lab.)"] # replace with "Firstname Lastname (Organization)"
		self.parent.helpText = """
		This is a scripted loadable module.
		It calculates the A-value, used to estimate Cochlear Duct Length."""
		self.parent.helpText += self.getDefaultModuleDocumentationLink()
		self.parent.acknowledgementText = """This process was developed at
		Western University in the Auditory Biophyiscs Lab """

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
		# Place Fiduicals & Align Volumes Button
		#
		self.fidButton			= qt.QPushButton("Place Fiduicals")
		self.fidButton.toolTip 	= "Place fiducials for volume alignment"
		self.fidButton.enabled	= False

		self.alignButton 	= qt.QPushButton("Align Volume")
		self.alignButton.toolTip = "Orient input volume to spatial region of Atlas"
		self.alignButton.enabled = False

		imageAlignment = qt.QHBoxLayout()
		imageAlignment.addWidget(self.fidButton)
		imageAlignment.addWidget(self.alignButton)
		parametersFormLayout.addRow("Image Alignment: ", imageAlignment)


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
		# self.outputTransformSelector.showHidden = False
		# self.outputTransformSelector.showChildNodeTypes = False
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
		self.fidButton.connect('clicked(bool)', self.onFidButton)
		self.alignButton.connect('clicked(bool)', self.onAlignButton)
		self.defineCropButton.connect('clicked(bool)', self.onDefineCropButton)
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
		self.fidButton.enabled = self.inputSelector.currentNode()
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

		#Display Atlas in 3D View
		sliceWidgetR 	= slicer.app.layoutManager().sliceWidget('Red')
		sliceWidgetY 	= slicer.app.layoutManager().sliceWidget('Yellow')
		sliceWidgetG 	= slicer.app.layoutManager().sliceWidget('Green')
		sliceLogicR = sliceWidgetR.sliceLogic()
		sliceLogicY = sliceWidgetY.sliceLogic()
		sliceLogicG = sliceWidgetG.sliceLogic()
		sliceNodeR = sliceLogicR.GetSliceNode()
		sliceNodeY = sliceLogicY.GetSliceNode()
		sliceNodeG = sliceLogicG.GetSliceNode()
		sliceNodeR.SetSliceVisible(True)
		sliceNodeY.SetSliceVisible(True)
		sliceNodeG.SetSliceVisible(True)

	def onFidButton(self):

		logging.info('Fiducial button selected')

		#Creat Markup node & add to scene
		self.placedLandmarkNode = slicer.vtkMRMLMarkupsFiducialNode()
		slicer.mrmlScene.AddNode(self.placedLandmarkNode)

		#Fiduical Placement Widget
		self.fiducialWidget = slicer.qSlicerMarkupsPlaceWidget()
		self.fiducialWidget.buttonsVisible = False
		self.fiducialWidget.placeButton().show()
		self.fiducialWidget.setMRMLScene(slicer.mrmlScene)
		self.fiducialWidget.setCurrentNode(self.placedLandmarkNode)
		self.fiducialWidget.placeMultipleMarkups = slicer.qSlicerMarkupsPlaceWidget.ForcePlaceSingleMarkup

		#Show fiducial placement Widget
		self.fiducialWidget.show()
		#Delay to ensure Widget Appears
		slicer.util.infoDisplay("Place the following fiducials in order:\n\n" +
		 						"- Oval Window\n- Cochlear Nerve\n- Apex\n- Round Window\n\n"+
								"Press okay when ready to begin" )

		#Enable alignment option
		self.alignButton.enabled = True

	def onAlignButton(self):

		logging.info('TODO - Align Button Code')

		self.LandmarkTrans = slicer.vtkMRMLTransformNode()
		slicer.mrmlScene.AddNode(self.LandmarkTrans)

		logic = AValue3DSlicerModuleLogic()

		if(self.placedLandmarkNode.GetNumberOfFiducials() == 4):
			logic.runFiducialRegistration(self.rightAtlas.isChecked(), self.LandmarkTrans, self.placedLandmarkNode)
		else:
			slicer.util.infoDisplay("4 Fiducials required for registration") #TODO - add appropriate information to help user!

		#Apply Landmark transform on Atlas Volume & Harden
		self.atlasVolume.SetAndObserveTransformNodeID(self.LandmarkTrans.GetID())
		slicer.vtkSlicerTransformLogic().hardenTransform(self.atlasVolume)


		self.defineCropButton.enabled	= True # enabled next step "Defining Crop region of interest"
		self.placedLandmarkNode.SetDisplayVisibility(0) #turn off display of placed landmarks -TODO - Is this needed


	def onDefineCropButton(self):

		self.atlasROI = slicer.vtkMRMLAnnotationROINode()
		self.atlasROI.Initialize(slicer.mrmlScene)
		self.atlasROI.SetRadiusXYZ(self.atlasVolume.GetOrigin()) #set origin of ROI

		slicer.mrmlScene.GetNodeByID(self.atlasVolume.GetID())

		slicer.app.layoutManager().setLayout(1) #Set to appropriate view (conventional)
		slicer.util.infoDisplay("Place the Region of Interest (ROI) shape over Atlas Volume.\n\n" +
		 						"NOTE: Ensure ROI encloses atlas in the Axial, Sagittal & Coronal views\n\n"+
								"Press okay when ready to begin" )

	def onCropButton(self):
		logic = AValue3DSlicerModuleLogic()
		#TODO - Carry out cropping of image

	def onApplyButton(self):

		#Instantiate logic class
		logic = AValue3DSlicerModuleLogic()

		#Run module logic
		logic.run(	self.inputSelector.currentNode(), self.outputSelector.currentNode(),
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

		#TODO - Make A-Value fiducials not visible in GUI
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

	# #Load Affine Transform - NOTE: method not used/required
	# def loadAffineTransform(self, aTransLocation = '/Users/JohnEniolu/Documents/AValueModuleData/Atlas_to_2R_RIG.h5'):
	# 	#load Affine transform
	# 	affineTrans = slicer.util.loadTransform(aTransLocation, returnNode=True)
	# 	return affineTrans[1] #Return Transform only
						   #TODO: Change file location to server location
	def loadAtlasLandmark(	self, isRight,
	 						landmarkLocationR = '/Users/JohnEniolu/Documents/AValueModuleData/initialLandmarkREG_R.fcsv',
							landmarkLocationL = '/Users/JohnEniolu/Documents/AValueModuleData/initialLandmarkREG_L.fcsv'):
		#Load fiducial landmark for initial atlas landmark registration
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

	def runCropVolume(self, roi, volume):
		#TODO - Crop volume

		#Define cropping node
		cropVolumeNode = slicer.vtkMRMLCropVolumeParametersNode()
		cropVolumeNode.SetScene(slicer.mrmlScene)
		cropVolumeNode.SetName('ChangeTracker_CropVolume_node')
		cropVolumeNode.SetIsotropicResampling(True)
		cropVolumeNode.SetSpacingScalingConst(0.5)
		slicer.mrmlScene.AddNode(cropVolumeNode)

		#Set volume and ROI required for cropping
		cropVolumeNode.SetInputVolumeNodeID(volume.GetID())
		cropVolumeNode.SetROINodeID(roi.GetID())

		#Apply Cropping
		cropVolumeLogic = slicer.modules.cropvolume.logic()
		cropVolumeLogic.Apply(cropVolumeNode)

		#TODO - Save cropped volume! - Which is it though!?
		return cropVolume

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
		cliParams = {'fixedVolume': inputVolume.GetID(), 'movingVolume': atlasVolume.GetID(),
						'bsplineTransform' : outputTrans.GetID() }
		cliParams.update({'samplingPercentage': 1, 'initialTransform' : self.linearTrans.GetID() })
		cliParams.update({'transformType': 'BSpline', 'splineGridSize': '3,3,3'})
		cliParams.update({'numberOfIterations' : 3000, 'minimumStepLength': 0.00001, 'maximumStepLength': 0.05})
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

		#Display Patient ID and Estimated A Valuee
		outputDisp = "Patient ID:\n" + inputVolume.GetName() + \
					"\n\nEstimated A Value:\n" + format(newAValue, '0.1f') + 'mm'
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

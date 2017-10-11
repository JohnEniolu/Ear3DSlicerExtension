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
		This is an example of scripted loadable module bundled in an extension.
		It performs a simple thresholding on the input volume and optionally captures a screenshot."""
		self.parent.helpText += self.getDefaultModuleDocumentationLink()
		self.parent.acknowledgementText = """This file was originally developed by Jean-Christophe Fillion-Robin,
		Kitware Inc.and Steve Pieper, Isomics, Inc.
		and was partially funded by NIH grant 3P41RR013218-12S1.""" # replace with organization, grant and thanks.

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
		parametersCollapsibleButton.text = "Parameters"
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
		# Align Volumes Button
		#
		self.alignButton = qt.QPushButton("Align Volume")
		self.alignButton.toolTip = "Orient input volume to spatial region of Atlas"
		self.alignButton.enabled = False
		parametersFormLayout.addRow(self.alignButton)

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
		self.outputTransformSelector.nodeTypes = ["vtkMRMLTransformNode"]
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
		parametersFormLayout.addRow("Output BSlpine Transform: ", self.outputTransformSelector)

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
		self.alignButton.connect('clicked(bool)', self.onAlignButton)
		self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
		self.outputTransformSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
		self.applyButton.connect('clicked(bool)', self.onApplyButton)

		# Add vertical spacer
		self.layout.addStretch(1)

		# Refresh Apply button state
		self.onSelect()

		# Refresh Ear Selection checkboxes state
		self.AtlasLoaded = False
		self.onLeftEarSelection()
		self.onRightEarSelection()

	def onSelect(self):

		# update status of apply Button
		self.alignButton.enabled = self.inputSelector.currentNode()
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

		self.AtlasLoaded = logic.runAtlasLoad(self.atlasSelection)


	def onAlignButton(self):
		#TODO - Interactive obtain fiducials from user to use in rigid (landmark) registration
		logging.info('TODO - Align Button Code')



	def onApplyButton(self):

		#Instantiate logic class
		logic = AValue3DSlicerModuleLogic()

		#Check atlas selection
		# if(self.rightAtlas.isChecked()):
		# 	self.atlasSelection = "right"
		# elif(self.leftAtlas.isChecked()):
		# 	self.atlasSelection = "left"
		# else:
		# 	self.atlasSelection = "none"

		#Run module logic
		logic.run(self.inputSelector.currentNode(), self.outputSelector.currentNode(),
					self.atlasSelection, self.outputTransformSelector.currentNode() )

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
									atlasLocation = '/Users/JohnEniolu/Documents/AValueModuleData/initialAtlasR.nrrd',
									fiducialLocation = '/Users/JohnEniolu/Documents/AValueModuleData/Atlas_AValue_F.fcsv'):
		#create atlasnode
		if isRight:
			atlasNode = slicer.util.loadVolume(atlasLocation, returnNode=True)
			atlasFiducial = slicer.util.loadMarkupsFiducialList(fiducialLocation, returnNode=True)
			logging.info('Loaded right ear atlas')
		else:
			#TODO - load the left atlas
			#atlasNode = slicer.util.loadVolume()
			#atlasFiducial = slicer.util.loadFiducialList(fiducialLocation, returnNode=True)
			logging.info('Loaded left ear atlas')
		return atlasNode, atlasFiducial

	#Load Affine Transform - NOTE: method not used/required
	def loadAffineTransform(self, aTransLocation = '/Users/JohnEniolu/Documents/AValueModuleData/Atlas_to_2R_RIG.h5'):
		#load Affine transform
		affineTrans = slicer.util.loadTransform(aTransLocation, returnNode=True)
		return affineTrans[1] #Return Transform only

	#Load atlas Landmarks - TODO: specify left or right landmark required/requested
						   #TODO: Change file location to server location
	def loadAtlasLandmark(self, landmarkLocation = '/Users/JohnEniolu/Documents/AValueModuleData/initialLandmarkREG.fscv'):
		#Load fiducial landmark for initial atlas landmark registration
		landmarkFid = slicer.util.loadFiducialList(landmarkLocation, returnNode=True)
		logging.info('loading landmarks')
		return landmarkFid[1]#Return fiducial only

	def printStatus(self):
		print('Fiduical placed!!')
		return True

	#Perform initial landmark registration for orientation
	def fiducialRegistration(self, atlas, rigTrans, inputVolume):
		#TODO - implement fiducial registration

		placeModePersistence = 0 # No persistence placing
		#movingLandmarkNode  = slicer.mrmlScene.GetNodeByID("vtkMRMLMarkupsFiducialNodeCochlea")
		#movingLandmarkNode.SetActivePlaceNodeID("vtkMRMLMarkupsFiducialNodeCochlea") #Create Fiducial Markup


		#Place 4 Fiducial for Cochlea Registration

		#Create node and add to scene
		#placedLandmarkNode = slicer.vtkMRMLMarkupsFiducialNode()
		#slicer.mrmlScene.AddNode(placedLandmarkNode)
		#placedLandmarks = slicer.modules.markups.logic().GetActiveListID() #retrieve user placed landmark

		#TODO - Figure a way to retrieve/poll user for the required landmarks for this registration!!***
		logging.info('start placing markups')

		# interactionNode = slicer.app.applicationLogic().GetInteractionNode()
		# selectionNode = slicer.app.applicationLogic().GetSelectionNode()
		# selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
		# placedLandmarkNode = slicer.vtkMRMLMarkupsFiducialNode()
		# slicer.mrmlScene.AddNode(placedLandmarkNode)
		# placedLandmarkNode.CreateDefaultDisplayNodes()
		# selectionNode.SetActivePlaceNodeID(placedLandmarkNode.GetID())
		# interactionNode.SetCurrentInteractionMode(interactionNode.Place)
		#interactionNode.AddObserver('PointClickedEvent', self.printStatus())
		#slicer.util.delayDisplay('Place oval window fiducial, then press okay.', 0)

		logging.info('done placing markups')

		#placedLandmarks = slicer.modules.markups.logic().GetActiveListID() #retrieve user placed landmark
		fixedLandmarkNode = self.loadAtlasLandmark()

		cliParamsFidReg = {'fixedPoints': fixedLandmarkNode,
						   	'movingPoints' : placedLandmarkNode,
							'transformType' : 'Rigid',
							'saveTransform' : rigTrans.GetID() }

		cliRigTrans = slicer.cli.run(slicer.modules.fiducialregistration, None,
									  cliParamsFidReg, wait_for_completion=True )

		#Apply Rigid transform on inputvolume
		#cliRegVolume = inputVolume.SetAndObserveTransformNodeID(outputTrans.GetID())
		#slicer.vtkSlicerTransformLogic().hardenTransform(self.atlasFiducial)
		#return cliRegVolume
		return cliRigTrans

	def cropVolume(self, atlas, volume):
		#TODO - Crop volume
		return cropVolume

	def runAtlasLoad(self, atlasSelection):

		#check atlas selection then retrive atlas
		if(atlasSelection != 'None'):
			if atlasSelection == 'right':
				self.loadedAtlas, self.loadFid 	= self.loadAtlasNodeAndFiducials(True) #Returns tuple
				self.atlasVolume  				= self.loadedAtlas[1] #Retrieve atlas Volume from tuple
				self.atlasFiducial 				= self.loadFid[1]
				return True
			elif atlasSelection == 'left':
				self.atlasVolume = self.loadAtlasNode(False)
				return True
			else:
				slicer.util.errorDisplay('Atlas not selected. Choose right or left ear atlas')
				return False

	#Automated A-value implementation
	def run(self, inputVolume, outputVolume, atlasSelection, outputTrans):
		"""
		Run the actual algorithm
		"""
		#check appropriate volume is selected
		if not self.isValidInputOutputData(inputVolume, outputVolume):
			slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
			return False

		#Run initial Landmark (Registration) Transformation Step 1
		#self.rigidInputVolume = fiducialRegistration( self.atlasVolume, outputTrans,
													  #inputVolume )
		self.rigTrans = self.fiducialRegistration( self.atlasVolume, outputTrans,
												inputVolume )

		#TODO - replace input volume with rigidInputVolume OR make output of fiducialRegistration
				# the initialTransfrom for the affine registration below!?!!

		#Set parameters and run affine registration Step 2
		cliParamsAffine = { 'fixedVolume' : inputVolume.GetID(),
							'movingVolume': self.atlasVolume,
							'linearTransform' : outputTrans.GetID() }
		cliParamsAffine.update({'samplingPercentage': 0.001,
								'initializeTransformMode' : 'useGeometryAlign',
								'transformType': 'Affine'})
		cliNode = slicer.cli.run(slicer.modules.brainsfit, None, cliParamsAffine, wait_for_completion=True)
		self.affineTransform = outputTrans.GetID() #Save Affine Transform output

		# Set parameters and run BSpline registration Step 3
		#TODO - Use Landmark registration result as the "initializeTransformMode" parameter
		cliParams = {'fixedVolume': inputVolume.GetID(), 'movingVolume': self.atlasVolume ,
						'bsplineTransform' : outputTrans.GetID() }
		cliParams.update({'samplingPercentage': 1, 'initialTransform' : self.affineTransform })
		cliParams.update({'transformType': 'BSpline', 'splineGridSize': '3,3,3'})
		cliParams.update({'numberOfIterations' : 3000, 'minimumStepLength': 0.0001, 'maximumStepLength': 0.05})
		cliParams.update({'costMetric' : 'NC' })
		cliNode = slicer.cli.run(slicer.modules.brainsfit, None, cliParams, wait_for_completion=True)



		#Apply BSpline transform on A-Value Fiducials
		self.atlasFiducial.SetAndObserveTransformNodeID(outputTrans.GetID())
		slicer.vtkSlicerTransformLogic().hardenTransform(self.atlasFiducial)

		#Calculate New A-Value
		numOfFids = self.atlasFiducial.GetNumberOfFiducials()
		fidXYZ_RW = [0,0,0] #Round Window placeholder
		fidXYZ_LW = [0,0,0] #Lateral Wall placeholder
		print numOfFids
		for index in range(numOfFids):
			if index == 0:
				self.atlasFiducial.GetNthFiducialPosition(index, fidXYZ_RW)
				print fidXYZ_RW
			else:
				self.atlasFiducial.GetNthFiducialPosition(index, fidXYZ_LW)
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

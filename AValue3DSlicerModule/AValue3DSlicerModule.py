import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

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
		# input volume selector
		#
		self.inputSelector = slicer.qMRMLNodeComboBox()
		self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
		self.inputSelector.selectNodeUponCreation = True
		self.inputSelector.addEnabled = False
		self.inputSelector.removeEnabled = False
		self.inputSelector.noneEnabled = False
		self.inputSelector.showHidden = False
		self.inputSelector.showChildNodeTypes = False
		self.inputSelector.setMRMLScene( slicer.mrmlScene )
		self.inputSelector.setToolTip( "select input image." )
		parametersFormLayout.addRow("Input Volume: ", self.inputSelector)

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
		# output volume selector - TODO: Make it the location of the atlas. user entered??
		#
		self.outputSelector = slicer.qMRMLNodeComboBox()
		self.outputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
		self.outputSelector.selectNodeUponCreation = True
		self.outputSelector.addEnabled = True
		self.outputSelector.removeEnabled = True
		self.outputSelector.noneEnabled = True
		self.outputSelector.showHidden = False
		self.outputSelector.showChildNodeTypes = False
		self.outputSelector.setMRMLScene( slicer.mrmlScene )
		self.outputSelector.setToolTip( "select output volume " )
		parametersFormLayout.addRow("Output Atlas Volume: ", self.outputSelector)

		#
		# Apply Button
		#
		self.applyButton = qt.QPushButton("Calculate A-Value")
		self.applyButton.toolTip = "Run the algorithm."
		self.applyButton.enabled = False
		parametersFormLayout.addRow(self.applyButton)

		# connections
		self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
		self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
		self.leftAtlas.connect('toggled(bool)', self.onLeftEarSelection)
		self.rightAtlas.connect('toggled(bool)', self.onRightEarSelection)
		self.applyButton.connect('clicked(bool)', self.onApplyButton)

		# Add vertical spacer
		self.layout.addStretch(1)

		# Refresh Apply button state
		self.onSelect()

		# Refresh Ear Selection checkboxes state
		self.onLeftEarSelection()
		self.onRightEarSelection()

	def onSelect(self):
		self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()

	def onLeftEarSelection(self):
		if self.leftAtlas.isChecked() == True:
			self.rightAtlas.setChecked(False)

	def onRightEarSelection(self):
		if self.rightAtlas.isChecked() == True:
			self.leftAtlas.setChecked(False)


	def onApplyButton(self):

		#Instantiate logic class
		logic = AValue3DSlicerModuleLogic()

		#Check atlas selection
		if(self.rightAtlas.isChecked()):
			self.atlasSelection = "right"
		elif(self.leftAtlas.isChecked()):
			self.atlasSelection = "left"
		else:
			self.atlasSelection = "none"

		#Run Atlas based on logic selection
		logic.run(self.inputSelector.currentNode(), self.outputSelector.currentNode(), self.atlasSelection)

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

	def loadAtlasNodeAndFiducials(self, isRight,
									atlasLocation = '/Users/JohnEniolu/Documents/AValueModuleData/1621R_20um-croppedAligned.nrrd',
									fiducialLocation = '/User/JohnEniolu/Documents/AValueModuleData/Atlas_AValue_F.fcsv'):
		#create atlasnode
		if isRight:
			atlasNode = slicer.util.loadVolume(atlasLocation, returnNode=True)
			atlasFiducial = slicer.util.loadFiducialList(fiducialLocation, returnNode=True)
			logging.info('Loaded right ear atlas')
		else:
			#TODO - load the left atlass
			#atlasNode = slicer.util.loadVolume()
			#atlasFiducial = slicer.util.loadFiducialList(fiducialLocation, returnNode=True)
			logging.info('Loaded left ear atlas')
		return atlasNode

	def loadAffineTransform(self, aTransLocation = '/Users/JohnEniolu/Documents/AValueModuleData/Atlas_to_2R_RIG.h5'):
		#load Affine transform
		affineTrans = slicer.util.loadTransform(aTransLocation, returnNode=True)
		return affineTrans[1] #Return Transform only

	def loadBsplineTransform(self, bTransLocation = '/Users/JohnEniolu/Documents/AValueModuleData/Atlas_to_2R_nonRIG.h5'):
		#load BSpline transform
		bsplineTrans = slicer.util.loadTransform(bTransLocation, returnNode=True)
		return bsplineTrans[1] #return Transform Only

	def run(self, inputVolume, outputVolume, atlasSelection):
		"""
		Run the actual algorithm
		"""
		#check atlas selection then retrive atlas
		if(atlasSelection != 'None'):
			if atlasSelection == 'right':
				self.loadedResult = self.loadAtlasNodeAndFiducials(True) #Returns tuple
				self.atlasVolume  = self.loadedResult[1] #Retrieve atlas Volume from tuple
			elif atlasSelection == 'left':
				self.atlasVolume = self.loadAtlasNode(False)
			else:
				slicer.util.errorDisplay('Atlas not selected. Choose right or left ear atlas')
				return False

		#check appropriate volume is selected
		if not self.isValidInputOutputData(inputVolume, outputVolume):
			slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
			return False
		#slicer.util.saveNode(outputVolume,'/Users/JohnEniolu/Documents/AValueModuleData/outputVolume')

		self.affineTransform 	= self.loadAffineTransform() #TODO - Can not load this, make it multilevel
		self.bSplineTransform 	= self.loadBsplineTransform() #TODO - Return a BSpline Transform!!

		# Create dictionary of required CLI parameters
		cliParams = {'fixedVolume': inputVolume.GetID(), 'movingVolume': self.atlasVolume, 'outputVolume' : outputVolume.GetID() }
		cliParams.update({'samplingPercentage': 1, 'initialTransform' : self.affineTransform, 'outputTransform': self.bSplineTransform })
		cliParams.update({ 'transformType': 'BSpline', 'useBSpline' : 1, 'splineGridSize': '3,3,3'})
		cliParams.update({'costMetric' : 'NC' })

		cliNode = slicer.cli.run(slicer.modules.brainsfit, None, cliParams, wait_for_completion=True)

		#TODO - Apply resulting transform to fiducials

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

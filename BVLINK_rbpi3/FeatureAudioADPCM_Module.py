from FeatureBase_Module import * 
import array
from collections import deque
import numpy as np

def _ST_UUID(val):
		with open('data_config.json', 'r') as f:
			 data = json.load(f)
		f.close()
		
		return UUID(val % int(data['audio_characteristic'],16) )
   		
class FeatureAudioADPCM(FeatureBase):
	
	def __init__(self, periph):
		FeatureBase.__init__(self, periph)
		self.charUUID=_ST_UUID(periph.serviceuuid)
		self.handle= periph.getCharacteristics(uuid=self.charUUID)[0].getHandle()
		self.engineADPCM=ADPCMEngine()
		self.dataPkt=[]
		self.audioPkt=deque()
		print("initAudioADPCM ")

	def getHandle(self):
		return self.handle
	
	def extractData(self, data):
		if len(data) != 20:
			raise NameError('error: pkt data length wrong')
		
		for b in data:
			self.dataPkt.append( self.engineADPCM.decode((b & 0x0F), self.SyncManager))
			self.dataPkt.append( self.engineADPCM.decode(((b >> 4) & 0x0F), self.SyncManager))	
			
		self.audioPkt.append(array.array('h', self.dataPkt).tostring())
		self.dataPkt.clear()
			
	def audio_stream(self, queue):
		if len(self.audioPkt) > 0:
			queue.append(self.audioPkt.popleft())
			
	def setSyncManager(self, m):
		self.SyncManager=m

#ADPCM Engine class. It contains all the operations and parameters necessary to decompress the
#audio received.

class ADPCMEngine(object):

	# Default Constructor
	def __init__(self): 
		#Quantizer step size lookup table 
		self.StepSizeTable=[7,8,9,10,11,12,13,14,16,17,
			19,21,23,25,28,31,34,37,41,45,
			50,55,60,66,73,80,88,97,107,118,
			130,143,157,173,190,209,230,253,279,307,
			337,371,408,449,494,544,598,658,724,796,
			876,963,1060,1166,1282,1411,1552,1707,1878,2066,
			2272,2499,2749,3024,3327,3660,4026,4428,4871,5358,
			5894,6484,7132,7845,8630,9493,10442,11487,12635,13899,
			15289,16818,18500,20350,22385,24623,27086,29794,32767];

		# Table of index changes 
		self.IndexTable = [-1,-1,-1,-1,2,4,6,8,-1,-1,-1,-1,2,4,6,8];
		self.index = 0;
		self.predsample = 0;


	 #* ADPCM_Decode.
	 #* @param code: a byte containing a 4-bit ADPCM sample.
	 #* @return : a struct which contains a 16-bit ADPCM sample

	def decode(self, code, syncManager): 

		if (syncManager is not None and syncManager.intra_flag):
			self.predsample = syncManager.getAdpcm_predsample_in();
			self.index = syncManager.getAdpcm_index_in();
			syncManager.reinitResetFlag();
		
		step = self.StepSizeTable[self.index];
		
		# 2. inverse code into diff 
		diffq = step>> 3;
		if ((code&4)!=0):
			diffq += step;
		
		if ((code&2)!=0):
			diffq += step>>1;
		

		if ((code&1)!=0):
			diffq += step>>2;

		# 3. add diff to predicted sample
		if ((code&8)!=0):
			self.predsample -= diffq;
		
		else:
			self.predsample += diffq;
		
		# check for overflow
		if (self.predsample > 32767):
			self.predsample = 32767;

		elif (self.predsample < -32768):
			self.predsample = -32768;

		# 4. find new quantizer step size 
		self.index += self.IndexTable [code];
		#check for overflow
		if (self.index < 0):
			self.index = 0;
			
		if (self.index > 88):
			self.index = 88;

		#5. save predict sample and index for next iteration 
		# done! static variables 

		# 6. return new speech sample
		return self.predsample;




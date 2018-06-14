import VirtualServerUtils
import os,sys,win32file,re,subprocess,win32com,win32wnet,time,shutil
from win32com.client import GetObject
import time, hashlib 
from abc import ABCMeta, abstractmethod

class OsHelper(object):
	__metaclass__ = ABCMeta
	
	def __new__(self,VMName,GuestOS):
		if(GuestOS == 'Windows'):
			return object.__new__(WindowsOShelper)
		
		if(GuestOS == "Unix"):
			return object.__new__(UnixOsHelper)
	
	def __init__(self,VMName,GuestOS):
		self.GuestOS = GuestOS
		self.VMName = VMName
		self.log = logger.get_log()
		self.SourceTestDataPath = VirtualServerUtils.Get_VSTestpath()
		self.wmiservice = None
		self.VMIP = None
		self.diskcount = 0
		self.SSHObject= None
		self.VolDetails={}
		self.DriveList = []
	
	@abstractmethod
	def GetVolInfo(self):
		self.log.info("This Gets all the Volume Info")
		
	@abstractmethod
	def GetDriveList(self):
		self.log.info("This Gets all the drivelist Info")
		
	@abstractmethod
	def CopyTestDataToEachVolume(self):
			self.log.info("This copies test data")
			
class WindowsOShelper(OsHelper):
	
	def __init__(self,VMName,GuestOS):
		super(WindowsOShelper,self).__init__(VMName,GuestOS)
		self.UserName = "%s\\Administrator"%self.VMName
		self.Password = "builder!12"
		self.IsLocal  = VirtualServerUtils.islocal(self.VMName)
		self.PreserveLevel = 1

	
	@property
	def VMUserName(self): return self.UserName
	
	@VMUserName.setter
	def VMUserName(self,UserName):
		self.UserName = UserName
	
	
	@property
	def VMPassword(self): return self.Password
	

	@VMPassword.setter
	def VMPassword(self,Password):
		self.Password = Password
		
	@property
	def DiskCount(self):
		self.getDiskCount()
		return self.diskcount
	
	@property
	def CURRENT_RUN_TIMESTAMP(self):
		return str(int(round(time.time(),0)))
	
	def SetRestorePath(self,Path):
		"""
		setting restore path
		"""
		try:
			VirtualServerUtils.CreateFolderIfnotExist(Path,True,self.VMName,self.UserName,self.Password)
			return Path
		
		except Exception,err:
			self.log.exception("Exception occurred in creating restore Path")
			raise Exception(err)
	
	def ConvertPathifRemote(self,path):
		"""
		convert the path if remote
		"""
		try:
			if not(self.IsLocal):
				location = remoteconnection.convert_unc(self.VMName,path)
				retcode = remoteconnection.wnet_connect(self.VMName, self.UserName, self.Password)
				if retcode!= True:
							log.info("wnet_connection failed")
		 
			else:
				 location = path
      
			return location
		
		except Exception,err:
			self.log.exception("Exception occurred in creating remote path")
			raise Exception(err)
				
	def GetwmiService(self):
		"""
		Get the wmi service for that VM
		"""
		try:
			objSWbemLocator = win32com.client.Dispatch("WbemScripting.SWbemLocator")
			
			if(self.IsLocal):
				self.wmiservice = objSWbemLocator.ConnectServer(self.VMName, "root\cimv2")
			
			else:
				self.wmiservice = objSWbemLocator.ConnectServer(self.VMName, "root\cimv2",self.UserName,self.Password)
		
		except Exception,err:
			self.log.exception("Exception occurred in getting the wmi service")
			raise Exception(err)
	
	def GetVolInfo(self):
		"""
		Get the Volume Info for VM
		"""
		try:
			if(self.wmiservice is None):
				self.GetwmiService()
			retry = 3
			while retry:
					try:
							retry -= 1
							wmiobj =  self.wmiservice.ExecQuery("select FreeSpace,Size,Name from Win32_LogicalDisk where DriveType=3")
							disk = 1
							for vol in wmiobj:
									self.VolDetails["Vol"+str(disk)] = {"Name": vol.Name, "FreeSpace=": vol.FreeSpace, "Size=": vol.Size}
									self.log.info("Volume Name and size are "+ str(vol.Name) +"  "+ str(vol.Size))
									disk += 1
							break
					except Exception,X:
							if retry:
									time.sleep(30)
									self.log.error("Retrying now, Error occured: " + str(X))
							else:
									self.log.error("All retries are over :/")
									raise X
			return self.VolDetails
		
		except Exception,err:
				self.log.exception("Exception while computing Remote Volume size or Connecting to Remote WMI")
				sys.stderr.write("Error %s\n" %str(err))
				return False
	
	def GetDriveList(self):
		"""
		Get the Drive list from the Volumes
		"""
		try:
			if(self.DriveList == []):
				if not(self.VolDetails):
					self.GetVolInfo()
					
				for key,val in self.VolDetails.iteritems():
						val = val['Name']
						self.DriveList.append(val)
				self.log.info(self.DriveList)
				if not (self.DriveList):
						raise Exception("drives details could not be obtained.")
				
			return self.DriveList
			
		except Exception,err:
				self.log.exception("Exception while computing Remote Volume size or Connecting to Remote WMI %s"%err)
				return False
	
	def CopyTestDataToEachVolume(self,Drive,DataTobeCopied,BackupFolderName):
		"""
		Copies testdata to each volume
		"""
		try:
			if(self.wmiservice is None):
				self.GetwmiService()
			_SourceFilePath = os.path.join(self.SourceTestDataPath,DataTobeCopied )              
			_DestPath = Drive+"\\TestData\\"+BackupFolderName+"\\"
			self.log.info("Copying Test Data to VM "+self.VMName+" for drive "+Drive)
			
			if not (self.VMIP is None):
				VMName = self.VMIP
			else:
				VMName = self.VMName
			_retcode = VirtualServerUtils.CopyToRemote(VMName, _SourceFilePath,_DestPath,self.UserName,self.Password)
			if (_retcode != 0):
				raise Exception
		
		except Exception,err:
			self.log.exception("An error occurred while copying tewstdata to volume")
			return False
	
	def CalculateChecksum(self,ChecksumPath,FolderName = None):
		try:
			Checksumdict = {}
			
			ChecksumPath = self.ConvertPathifRemote(ChecksumPath)
			if not (FolderName is None):
				FolderResPath = ChecksumPath+"\\"+FolderName
				if(os.path.exists(FolderResPath)):
					ChecksumPath = FolderResPath
				
			self.log.info("Going to check checksum for %s"%ChecksumPath)
			for dirpath, dirnames, filenames in os.walk(ChecksumPath):
					for eachfile in filenames:
							filepath = os.path.join(dirpath,eachfile)
							f = open(filepath,'rb')
							m = hashlib.md5()
							while True:
									data = f.read(10240)
									if len(data) == 0:
											break
									m.update(data)
							f.close()
							file_chksum =  m.hexdigest()
							filekey = filepath.split(ChecksumPath)[1]
							filekey = filekey.replace("\\","/")
							Checksumdict[filekey] = file_chksum
							
			self.log.info("Source chekcsum is %s"%Checksumdict)
			return Checksumdict
		
		except Exception,e:
			self.log.exception("An exception Occurred in calculating the checksum of windows directory")
			raise e
	
	def ListDiskInPath(self,DiskRestorePath,DiskExtension):
		"""
		list all the disk in path
		"""
		try:
			_Disklist = []
			DiskRestorePath = self.ConvertPathifRemote(DiskRestorePath)
			self.log.info("Restore path provided ot check is %s"%DiskRestorePath)
			_RestorePathfiles = os.listdir(DiskRestorePath)
			self.log.info("Disk present in path are %s"%_RestorePathfiles)
			
			for eachdisk in _RestorePathfiles:
					if any(ext in eachdisk.lower() for ext in DiskExtension):
						_diskpath = os.path.join(DiskRestorePath,eachdisk)
						_Disklist.append(_diskpath.rstrip())
			
			return _Disklist
	
		except Exception,e:
			self.log.exception("An exception Occurred in cListDiskInPath")
			raise e
	
	def ReadTextFile(self,txtFilePath):
		"""
    Reads the  text file adn returns as List
    """
		try:
			if(not(self.IsLocal)):
				_SrcPath = self.ConvertPathifRemote(txtFilePath)
			
			else:
				_SrcPath =txtFilePath
				
			with open (_SrcPath, "r") as myfile:
					data=myfile.readlines()
	
			return data
			
		except:
			self.log.exception("Exception raised at ReadTextFile")
			return False
	
	def getFilesinPath(self,Path):
		"""
		list all the files  in path
		"""
		try:
			_FileList = []
			_SrcPath = self.ConvertPathifRemote(Path)
			self.log.info(" path provided ot check is %s"%_SrcPath)
			_FileList = os.listdir(_SrcPath)
			self.log.info("Files present in path are %s"%_FileList)
			return _FileList

	
		except Exception,e:
			self.log.exception("An exception Occurred in getFilesinPath")
			raise e
	
	def CopyEXEToMachine(self, localPath,RemotePath):
		"""
		copy exe to the machine
		"""
		try:
			DestPath = self.ConvertPathifRemote(RemotePath)
			shutil.copy(localPath,DestPath)
		
		except Exception,e:
			self.log.exception("An exception Occurred in CopyEXEToMachine")
			raise e
					
	def getDiskCount(self):
		"""
		get the count of physical disk in proxy
		"""
		try:
			
			if(self.wmiservice is None):
				self.GetwmiService()
				
			_diskobj = self.wmiservice.ExecQuery("select * from Win32_PhysicalMedia")
			disks = 0
			for disk in _diskobj:
				disks= disks+1
			
			self.diskcount = disks
	
		except Exception,e:
			self.log.exception("An exception Occurred in getDiskCount")
			raise e
	
	def CopyOnRemoteAndExecute(self,filesToCopy,filebasename,destDir):
		"""
		Copies the Batch file on remote machine and executes the qscript.
		"""
		try:
			for f2c in filesToCopy:
				copied  =   False
				count   =   0
				while (not(copied==True)) and (count<10):
						count = count + 1
						_retCode,_retString = self.copyFileToMachine(f2c[1],f2c[0],destDir)
						if (_retCode !=0):
								self.log.warning(_retString)
								self.log.info("Re-trying copy to Machine in 10 seconds.")
								time.sleep(10)
						else:
								copied = True
				else:
						if not (copied):
								raise Exception("Exceeded maximum number of copy attemps, so file cannot be excuted.")

				time.sleep(5)
				Executescript =   False
				_retCode,_retString = self.runScript(filebasename,filePath = destDir)
				return _retCode,_retString
	
		except Exception,err:
			self.log.exception("An exception occurred while excuting the script")
			raise err

	def copyFileToMachine(self,filePath,file=None,destDir = ''):
		"""
    copy this file to remote machine
    """
		try:   

				retCode, returnString = remoteconnection.netCopy(self.VMName, self.UserName, self.Password, filePath, destDir, move = False, highDebug=False)				
				self.log.info("Successfully copied the File to remote machine")
				return retCode, returnString
        
		except Exception,err:
			self.log.exception("Exception in copyInstallFileToMachine")
			raise err

	def runScript(self,file,filePath = None,destDir = None):
		"""
		Run script on the machine
		"""
		try:   
			
			
			
			_ReturnCode   = None
			returnString  = None
			self.log.info("Running the File:[%s] Src Path:[%s]  Destination Dir:[%s]   on Machine:[%s]"%(file,filePath,destDir,self.VMName))
			UserName = self.UserName.split("\\")[1]
			
			if(self.IsLocal):
				destDir = VirtualServerUtils.GetVSAXMLPath()
				
			
			else:
				destDir = filePath
			
			_outputPipeLoc = os.path.join(destDir,"PSEXEC_OUTPUT_"+self.CURRENT_RUN_TIMESTAMP+".txt")
			#VirtualServerUtils.CreateFolderIfnotExist(_outputPipeLoc)

			
			_ReturnCode, returnString = remoteconnection.executeOnRemoteMachine(self.VMName,
															os.path.join(filePath,file), UserName, self.Password, captureOutputPipes = True,
															outputPipeLoc = _outputPipeLoc,highDebug = True)
					
			self.log.info(" Return Code is %s "%(_ReturnCode))
			

			returnString = 	self.ReadTextFile(_outputPipeLoc)
				
			return _ReturnCode,returnString
        
		except Exception,err:
			self.log.exception("Exception in runScript: %s" % str(err))
			raise err
		
	def FindFileParticularExtension(self,Path,Extension):
		"""
		Find the file ofgiven extension
		"""
		try:
			FileName = None
			_FilesinPath = self.getFilesinPath(Path)
			for EachFile in _FilesinPath:
				if(EachFile.endswith(Extension)):
					FileName = EachFile
					break
			
			if(FileName is None):
				raise Exception("no file found with that extension")
			
			else:
				return FileName
		
		except Exception , err:
			self.log.exception("An error Occurred in Getting the file of Particualr extension")
			return False

	
class UnixOsHelper(OsHelper):
	
	def __init__(self,VMName,GuestOS):
		super(UnixOsHelper,self).__init__(VMName,GuestOS)
		self.UserName = "root"
		self.Password = "builder!12"
		self.PreserveLevel = 2
		self.sshConn = None
		
		@property
		def VMUserName(self): return self.UserName
	
		@VMUserName.setter
		def VMUserName(self,Uname):
			self.UserName = Uname
		
		@property
		def VMPassword(self): return self.Password
	
		@VMPassword.setter
		def VMUserName(self,Pwd):
			self.Password = Password
		
	
	def GetSSHObject(self):

		self.sshConn = None
		try:
				for i in range (0,3):
						try:	
								x = i + 1
								self.log.info("Attempt %d" % x)
								self.sshConn=remoteconnection.Connection(self.VMName, OS="unix", username=self.UserName, password=self.Password)
								break
						except:
								self.log.exception("Could not establish connection")
								time.sleep(120)
								continue
						
				if not self.sshConn:
						self.log.info("ERROR in establishing Connection")
						raise Exception
					
		except Exception, X:
				self.log.exception("ERROR - exception while creating ssh connection with unix VM:"+str(X))
				return False
	
	def SetRestorePath(self,Path):
		"""
		set the restore Path
		"""
		try:
			if(self.sshConn is None):
					self.GetSSHObject()
				

			_removecmd = "rm -rf %s"%Path
			(retcode,value) = self.sshConn.execute(_removecmd)
			if(retcode != 0):
					self.log.info("remove folder was not successful")
			
			_createcmd = "mkdir %s"%_path
			(retcode,value) = self.sshConn.execute(_removecmd)
			if(retcode != 0):
					self.log.info("create folder was not successful")
			
		
		except Exception, X:
				self.log.exception("ERROR - exception while setting restore path with unix VM:"+str(X))
				return False
	
	def GetVolInfo(self):
		"""
		Get the VOlume Info for the VM
		"""
    
		self.VolDetails={}
		try:
				
				if(self.sshConn is None):
					self.GetSSHObject()
					
				index = 1
				cmd = 'mount |cut -f1,3,5 -d\' \''
				self.log.info("Command to Execute:"+cmd)
				(retCode,volumes) = self.sshConn.execute(cmd)
				self.log.info("resCode is " + str(retCode))
				self.log.info("Output from the command [%s] is [%s] "%(cmd,str(volumes)))
				if retCode != 0:
						raise Exception           
				for volumeinfo in volumes:
						volume=volumeinfo.split(' ')
						FileSystem=volume[2].strip()
						MountPoint=volume[1]
						BaseDevice=volume[0]
					 
						if BaseDevice.find("/dev/sd") >= 0 :
								self.VolDetails["MountDir-"+str(index)]=volume[1]
								self.log.info("Added an UnNamed Volume[%s] with mount point [%s] type :[%s] to the backup list"%(str(index),volume[1],volume[2].strip()))
								index=index+1
						
						if BaseDevice.find("/dev/mapper") >= 0 :
								_volname = BaseDevice.split("/")[-1]
								self.VolDetails[_volname]=MountPoint
								self.log.info("Added Volume[%s] with mount point [%s] type :[%s] to the backup list"%(volume[0],volume[1],volume[2].strip())) 
											
				if not (self.VolDetails):
						self.log.info("No Volumes are discovered to Backup.Returning False.")
						raise Exception
				
				return self.VolDetails
		
		except Exception,X:
				self.log.Exception ("An error Occurred in getting Volume Details  %s"%X)
				return False
	
	def GetDriveList(self):
		"""
		Get the Drive list for the VM
		"""
		try:
			if(self.DriveList == []):
				if not(self.VolDetails):
					self.GetVolInfo()
			
			for volname,vol in self.VolDetails.iteritems():
				self.DriveList.append(volname)
			
			self.log.info(self.DriveList)
			if not (self.DriveList):
					raise Exception("drives details could not be obtained.")
			
			return self.DriveList	
		
		except Exception,err:
				self.log.Exception ("An error Occurred in getting Volume Details  %s"%err)
				return False
	
	def CopyTestDataToEachVolume(self,Drive,DataTobeCopied,BackupFolderName):
		"""
		Copies testdata to each volume in Unix
		"""
		try:
			  
				if(self.sshConn is None):
					self.GetSSHObject()
				self.log.info("copying  Test Data Folder.")
				
				Drive = self.VolDetails[Drive]
				
				_SourceFilePath = os.path.join(self.SourceTestDataPath,DataTobeCopied)
				
				if(Drive == "/"):
					_DestMountPath = Drive+"TestData/"
				else:
					_DestMountPath = Drive+"/TestData/"
				
				_cmd = "mkdir %s"%_DestMountPath
				(_retcode,value) = self.sshConn.execute(_cmd)
				if(_retcode != 0):
						self.log.info("Directory creation failed")
						
				
				_cmd = r"echo y | PSCP.exe -pw " +self.Password+ " " + "-r" +" "+ '"' + _SourceFilePath + '"' + r" root@"+self.VMName+":"+_DestMountPath
				self.log.info("Command to be executed is %s"%_cmd)
				Count = 0
				_retCode = False
				
				while(Count<3):
						_retcode,output = cmdhelper.executeCommand(_cmd,retryMaxQty=1,highDebug = True,baseDir = self.basedir)
						if str(output).find("100%") > 0:
								self.log.info("files copied successfully")
								_retCode = True
								break
								
						else:
								self.log.info("[Error ] :: " + str(output))
								Count = Count+1
				
				if not(	_retCode):
					raise Exception("Copying testdata failed")
				
						
		except Exception,X:
				self.log.exception("An error Occurred in copying  testdata %s"%X)
				raise  X
	
	def CalculateChecksum(self,ChecksumPath,FolderName = None):
		try:
			
			if(self.sshConn is None):
					self.GetSSHObject()
					
			Checksumdict = {}
			if not(FolderName is None):
				ChecksumPath = ChecksumPath+"/"+FolderName
				
			ListCmd = "find %s -type f"%ChecksumPath
			self.log.info("Checksum Path to be lsited with command is %s"%ListCmd)
			(retcode,files) = self.sshConn.execute(ListCmd)
			for eachfile in files:
					checksumcommand = "md5sum %s"%eachfile
					self.log.info("Checksum command is %s"%checksumcommand)
					(retcode,chksumval) = self.sshConn.execute(checksumcommand)
					filekey = eachfile.split(ChecksumPath)[1]
					Checksumdict[filekey] = chksumval.split(' ')[0]
			
			self.log.info("Checksum dict in unix is %s"%Checksumdict)
			return Checksumdict
    
		except Exception,e:
			self.log.exception("An exception Occurred in calculating the checksum of windows directory")
			raise e
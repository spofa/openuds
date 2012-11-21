# -*- coding: utf-8 -*-

#
# Copyright (c) 2012 Virtual Cable S.L.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, 
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice, 
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice, 
#      this list of conditions and the following disclaimer in the documentation 
#      and/or other materials provided with the distribution.
#    * Neither the name of Virtual Cable S.L. nor the names of its contributors 
#      may be used to endorse or promote products derived from this software 
#      without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''
.. moduleauthor:: Adolfo Gómez, dkmaster at dkmon dot com
'''

from uds.core.services import UserDeployment
from uds.core.util.State import State
import logging

logger = logging.getLogger(__name__)

opCreate, opStart, opStop, opSuspend, opWait, opError, opFinish, opRetry = range(8)

class OVirtLinkedDeployment(UserDeployment):
    '''
    This class generates the user consumable elements of the service tree.
    
    After creating at administration interface an Deployed Service, UDS will
    create consumable services for users using UserDeployment class as
    provider of this elements.
    
    The logic for managing ovirt deployments (user machines in this case) is here.
    
    '''
    
    #: Recheck every five seconds by default (for task methods)
    suggestedTime = 5

    def initialize(self):
        self._name = ''
        self._ip = ''
        self._vmid = ''
        self._reason = ''
        self._queue = []
        self._destroyAfter = 'f'

    # Serializable needed methods        
    def marshal(self):
        '''
        Does nothing right here, we will use envoronment storage in this sample
        '''
        return ''
    
    def unmarshal(self, str_):
        '''
        Does nothing here also, all data are keeped at environment storage
        '''
        pass
    

    def getName(self):
        '''
        We override this to return a name to display. Default inplementation 
        (in base class), returns getUniqueIde() value
        This name will help user to identify elements, and is only used
        at administration interface.
        
        We will use here the environment name provided generator to generate
        a name for this element.
        
        The namaGenerator need two params, the base name and a length for a 
        numeric incremental part for generating unique names. This are unique for
        all UDS names generations, that is, UDS will not generate this name again
        until this name is freed, or object is removed, what makes its environment
        to also get removed, that makes all uniques ids (names and macs right now)
        to also get released.
        
        Every time get method of a generator gets called, the generator creates
        a new unique name, so we keep the first generated name cached and don't
        generate more names. (Generator are simple utility classes)
        '''
        if self._name  == '':
            self._name = self.nameGenerator().get( self.service().getBaseName(), self.service().getLenName() )
        return self._name 

    
    def setIp(self, ip):
        '''
        In our case, there is no OS manager associated with this, so this method
        will never get called, but we put here as sample.
        
        Whenever an os manager actor notifies the broker the state of the service
        (mainly machines), the implementation of that os manager can (an probably will)
        need to notify the IP of the deployed service. Remember that UDS treats with
        IP services, so will probable needed in every service that you will create.
        :note: This IP is the IP of the "consumed service", so the transport can
               access it.
        '''
        logger.debug('Setting IP to %s' % ip)
        self._ip = ip
    
    def getUniqueId(self):
        '''
        Return and unique identifier for this service.
        In our case, we will generate a mac name, that can be also as sample
        of 'mac' generator use, and probably will get used something like this
        at some services.
        
        The get method of a mac generator takes one param, that is the mac range
        to use to get an unused mac.
        '''
        if self._mac == '':
            self._mac =  self.macGenerator().get( self.service().getMacRange() )
        return self._mac
    
    def getIp(self):
        '''
        We need to implement this method, so we can return the IP for transports
        use. If no IP is known for this service, this must return None
        
        If our sample do not returns an IP, IP transport will never work with
        this service. Remember in real cases to return a valid IP address if
        the service is accesible and you alredy know that (for example, because
        the IP has been assigend via setIp by an os manager) or because
        you get it for some other method.  
        
        Storage returns None if key is not stored.
        
        :note: Keeping the IP address is responsibility of the User Deployment.
               Every time the core needs to provide the service to the user, or
               show the IP to the administrator, this method will get called
               
        '''
        return self._ip

    def setReady(self):
        '''
        The method is invoked whenever a machine is provided to an user, right
        before presenting it (via transport rendering) to the user.
        '''
        if self.cache().get('ready') == '1':
            return State.FINISHED
        
        state = self.service().getMachineState(self._vmid)
        
        if state == 'unknown':
            return self.__error('Machine is not available anymore')
        
        if state not in ('up', 'powering_up', 'restoring_state'):
            return self.__powerOn()
        
        self.cache().put('ready', '1')
        return State.FINISHED

    def notifyReadyFromOsManager(self, data):
        # Here we will check for suspending the VM (when full ready)
        logger.debug('Checking if cache 2 for {0}'.format(self._name))
        if self.__getCurrentOp() == opWait:
            logger.debug('Machine is ready. Moving to level 2')
            self.__popCurrentOp() # Remove current state
            return self.__executeQueue()
            
        #if self._squeue.getCurrent() == stWaitReady:
        #    logger.debug('Move to level 2, suspending machine')
        #    return self.moveToCache(self.L2_CACHE)
        return State.FINISHED
    
    def __executeQueue(self):
        op = self.__getCurrentOp()
        
        if op == opError:
            return State.ERROR
        
        if op == opFinish:
            return State.FINISHED
        
        if op == opCreate:
            return self.__create()
    
    def __initQueueForDeploy(self, forLevel2 = False):
        
        if forLevel2 is False:
            self._queue = [opCreate, opStart, opFinish]
        else:
            self._queue = [opCreate, opStart, opWait, opSuspend, opFinish]
        
    def __getCurrentOp(self):
        if len(self._queue) == 0:
            return opFinish
        
        return self._queue[0]
    
    def __popCurrentOp(self):
        if len(self._queue) == 0:
            return opFinish
        
        res = self._queue.pop(0)
        return res
    
    def __pushFrontOp(self, op):
        self._queue.insert(0, op)
        
    def __pushBackOp(self, op):
        self._queue.append(op)
    
    def __error(self, reason):
        '''
        Internal method to set object as error state
        
        Returns:
            State.ERROR, so we can do "return self.__error(reason)"
        '''
        self._queue = [opError]
        self._reason = str(reason)
        return State.ERROR
    
    # Queue execution methods
    def __retry(self):
        '''
        Used to retry an operation
        In fact, this will not be never invoked, unless we push it twice, because
        checkState method will "pop" first item when a check operation returns State.FINISHED
        '''
        return State.FINISHED
    
    def __create(self):
        '''
        Deploys a machine from template for user/cache
        '''
        templateId =  self.publication().getTemplateId()
        name = self.service().sanitizeVmName('UDS service ' + self.getName())
        comments = 'UDS Linked clone for'
        
        try:
            self._vmid = self.service().deployFromTemplate(name, comments, templateId)
            if self._vmid is None:
                raise Exception('Can\'t create machine')
        except Exception as e:
            return self.__error(e)
        
        return State.RUNNING
    
    def __powerOn(self):
        '''
        Powers on the machine
        '''
        state = self.service.getMachineState(self._vmid)
        if state == 'down':
            pass
        
    def deployForUser(self, user):
        '''
        Deploys an service instance for an user.
        '''
        self.__initQueueForDeploy(False)
        return self.__executeQueue()
    
    def deployForCache(self, cacheLevel):
        '''
        Deploys an service instance for cache
        '''
        forLevel2 = cacheLevel == self.L2_CACHE 
        self.__initQueueForDeploy(forLevel2)
        return self.__executeQueue()
    
    def __checkDeploy(self):
        '''
        Checks the state of a deploy for an user or cache
        '''
        try:
            state = self.service().getMachineState(self._vmid)
            if state != 'down':
                return State.RUNNING
        except Exception as e:
            return self.__error(e)
        
        return State.FINISHED
            
    
    def checkState(self):
        '''
        Check what operation is going on, and acts acordly to it
        '''
        op = self.__getCurrentOp()
        
        if op == opError:
            return State.ERROR
        
        if op == opFinish: 
            return State.FINISHED
        
        res = None
        
        if op == opCreate:
            res = self.__checkDeploy()
        
        if op == opStart:
            res = self.__checkPowerOn()
            
        if op == opStop:
            res = self.__checkPowerOff()
            
        if op == opWait:
            res = State.RUNNING
            
        if op == opSuspend:
            res = self.__checkSuspend()

        if res is None:
            return self.__error('Unexpected operation found')
            
        if res == State.FINISHED:
            self.__popCurrentOp()
            return State.RUNNING
        return res
        
    
    def finish(self):
        '''
        Invoked when the core notices that the deployment of a service has finished.
        (No matter wether it is for cache or for an user)
        
        This gives the oportunity to make something at that moment.
        :note: You can also make these operations at checkState, this is really
        not needed, but can be provided (default implementation of base class does
        nothing) 
        '''
        # Note that this is not really needed, is just a sample of storage use
        self.storage().remove('count')
        
    def assignToUser(self, user):
        '''
        This method is invoked whenever a cache item gets assigned to an user.
        This gives the User Deployment an oportunity to do whatever actions
        are required so the service puts at a correct state for using by a service.
        
        In our sample, the service is always ready, so this does nothing.
        
        This is not a task method. All level 1 cache items can be diretly
        assigned to an user with no more work needed, but, if something is needed,
        here you can do whatever you need
        '''
        pass
    
    def userLoggedIn(self, user):
        '''
        This method must be available so os managers can invoke it whenever
        an user get logged into a service.
        
        Default implementation does nothing, so if you are going to do nothing,
        you don't need to implement it.
        
        The responability of notifying it is of os manager actor, and it's 
        directly invoked by os managers (right now, linux os manager and windows
        os manager)
        
        The user provided is just an string, that is provided by actor.
        '''
        # We store the value at storage, but never get used, just an example
        self.storage().saveData('user', user)
        
    def userLoggedOut(self, user):
        '''
        This method must be available so os managers can invoke it whenever
        an user get logged out if a service.
        
        Default implementation does nothing, so if you are going to do nothing,
        you don't need to implement it.
        
        The responability of notifying it is of os manager actor, and it's 
        directly invoked by os managers (right now, linux os manager and windows
        os manager)
        
        The user provided is just an string, that is provided by actor.
        '''
        # We do nothing more that remove the user
        self.storage().remove('user')
    
    def reasonOfError(self):
        '''
        Returns the reason of the error.
        
        Remember that the class is responsible of returning this whenever asked
        for it, and it will be asked everytime it's needed to be shown to the
        user (when the administation asks for it).
        '''
        return self.storage().readData('error') or 'No error'
    
    def destroy(self):
        '''
        This is a task method. As that, the excepted return values are
        State values RUNNING, FINISHED or ERROR.
        
        Invoked for destroying a deployed service
        Do whatever needed here, as deleting associated data if needed (i.e. a copy of the machine, snapshots, etc...)
        @return: State.FINISHED if no more checks/steps for deployment are needed, State.RUNNING if more steps are needed (steps checked using checkState)
        ''' 
        return State.FINISHED

    def cancel(self):
        '''
        This is a task method. As that, the excepted return values are
        State values RUNNING, FINISHED or ERROR.
        
        This can be invoked directly by an administration or by the clean up
        of the deployed service (indirectly).
        When administrator requests it, the cancel is "delayed" and not
        invoked directly.
        '''
        return State.FINISHED
        
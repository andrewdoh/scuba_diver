import MalmoPython
import os
import sys
import time
import json
import random
import math
from timeit import default_timer as timer

saved_filename = "C:\Users\Caitlin\Documents\CS175\WaterWorld"
mission_xml = '''<?xml version="1.0" encoding="UTF-8" ?>
    <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <About>
            <Summary>Load a world</Summary>
        </About>
        <ModSettings>
            <MsPerTick>100</MsPerTick>
        </ModSettings>
        <ServerSection>
            <ServerInitialConditions>
                <Time>
                    <StartTime>1000</StartTime>
                    <AllowPassageOfTime>false</AllowPassageOfTime>
                </Time>
                <Weather>clear</Weather>
            </ServerInitialConditions>
            <ServerHandlers>
                <FileWorldGenerator src="''' + saved_filename + '''"/>
		<ServerQuitFromTimeUp timeLimitMs="100000"/>
                <ServerQuitWhenAnyAgentFinishes />
            </ServerHandlers>
        </ServerSection>
        <AgentSection mode="Survival">
            <Name>Naruto</Name>
            <AgentStart>
                <Placement x="1142.5" y="25" z="-481.5"/>
            </AgentStart>
            <AgentHandlers>
                <ObservationFromFullStats/>
                <AbsoluteMovementCommands/>
                <DiscreteMovementCommands/>
                <MissionQuitCommands/>
                <RewardForCollectingItem>
                    <Item type="emerald" reward="1"/>
                </RewardForCollectingItem>
                <RewardForTouchingBlockType>
                    <Block reward="100.0" type="redstone_block" behaviour="onceOnly"/>
                </RewardForTouchingBlockType>
                <RewardForSendingCommand reward="-1"/>
                <ObservationFromGrid>
                    <Grid name="floorAll">
                        <min x="-1" y="-4" z="-1"/>
                        <max x="1" y="4" z="1"/>
                    </Grid>
                </ObservationFromGrid>
            </AgentHandlers>
        </AgentSection>
    </Mission>'''



class UnderwaterAgent(object):
    def __init__(self,alpha=1,gamma=1,n=1):
        self.epsilon = 0.1
        self.q1_table = {} #value of state
        self.q2_table = {} #value of advantage/action
        self.n,self.alpha,self.gamma = n,alpha,gamma

        self.curr_x = 0
        self.curr_y = 0
        self.curr_z = 0
        self.sent_tp = False
        self.training = True


    def teleport(self, agent_host, move_up):
        """Directly teleport to a specific position."""

        move_by = 4
        if move_up:
            tel_y= self.curr_y+move_by 
        else:
            tel_y= self.curr_y-move_by 
        tp_command = "tp {} {} {}".format(self.curr_x,tel_y,self.curr_z)
        #print("X,Y,Z----: {},{},{}".format(self.curr_x,tel_y,self.curr_z))
        return tp_command
        '''agent_host.sendCommand(tp_command)
        good_frame = False
        start = timer()
        while not good_frame:
            world_state = agent_host.getWorldState()
            if not world_state.is_mission_running:
                print "Mission ended prematurely - error."
                exit(1)
            if not good_frame and world_state.number_of_video_frames_since_last_state > 0:
                frame_x = world_state.video_frames[-1].xPos
                frame_z = world_state.video_frames[-1].zPos
                if math.fabs(frame_x - teleport_x) < 0.001 and math.fabs(frame_z - teleport_z) < 0.001:
                    good_frame = True
                    end_frame = timer()'''
        

    def get_possible_actions(self, world_state,agent_host):
        """Returns all possible actions that can be done at the current state. """
        action_list = []
        possibilities = {'movenorth 1': -3,'movesouth 1': 3,'moveeast 1': 1,'movewest 1': -1}
        #check walls to see whether can move left,right,back,forward
        #check floor beneath to see whether should do anything at all, or just nothing and sink
        obs_text = world_state.observations[-1].text
        obs = json.loads(obs_text)
        grid = load_grid(world_state)

        for k,v in possibilities.items():
            #index 22 will always be where our agent is standing in the beginning with the current setup
            if grid[31+v+9] != 'sea_lantern' and grid[22+v+9] != 'glowstone':
                action_list.append(k)
        if grid[31-27] == 'water' or grid[31-27] == 'wooden_door':
            action_list.append(self.teleport(agent_host,False))
        if grid[31+45] == 'water' or grid[31+45] == 'wooden_door':
            action_list.append(self.teleport(agent_host,True))

        print("ACTION LIST: {}".format(action_list))
        return action_list

    def act(self,world_state,agent_host,current_reward):
        
        obs_text = world_state.observations[-1].text
        obs = json.loads(obs_text)
        curr_state = "%d.%d.%d" % (int(obs[u'XPos']),int(obs[u'YPos']), int(obs[u'ZPos']))

        #update both if action doesn't exist in one.. (so they always exist in both)
        ########3CURRENTLY USING ONLY ONE Q TABLE. CHANGE.##########
        if curr_state not in self.q1_table:
            self.q1_table[curr_state] = ([0] * len(self.get_possible_actions(world_state,agent_host)))
        '''    self.q2_table[curr_state] = {}
        for action in possible_actions:
            if action not in self.q1_table[curr_state]:
                self.q1_table[curr_state][action] = 0
                self.q2_table[curr_state][action] = 0'''

        # update Q values
        if self.training and self.prev_s is not None and self.prev_a is not None:
            old_q = self.q1_table[self.prev_s][self.prev_a]
            self.q1_table[self.prev_s][self.prev_a] = old_q + self.alpha * (current_reward
                + self.gamma * max(self.q1_table[curr_state]) - old_q)
        
        #select next action
        possible_actions = self.get_possible_actions(world_state,agent_host)
        a = self.choose_action(curr_state,possible_actions)

        #send selected action
        print("\n--TOOK ACTION: {}".format(possible_actions[a]))
        if possible_actions[a].find("tp")!=-1:
            self.sent_tp = True
        agent_host.sendCommand(possible_actions[a])
        '''if self.sent_tp:
            split_string = possible_actions[a].split(' ')
            good_frame = False
            start = timer()
            while not good_frame:
                world_state = agent_host.getWorldState()
                if not world_state.is_mission_running:
                    print "Mission ended prematurely - error."
                    exit(1)
                if not good_frame and world_state.number_of_video_frames_since_last_state > 0:
                    frame_x = world_state.video_frames[-1].xPos
                    frame_z = world_state.video_frames[-1].zPos
                    if math.fabs(frame_x - float(split_string[1])) < 0.001 and math.fabs(frame_z - float(split_string[3])) < 0.001:
                        good_frame = True
                        end_frame = timer()
            self.sent_tp = False #yeah?'''
        self.prev_s = curr_state
        self.prev_a = a
        
        return current_reward
                
    
    def choose_action(self,curr_state,possible_actions):

        rnd = random.random()
        if rnd < self.epsilon:
            rnd = random.random()
            a = random.randint(0,len(possible_actions) - 1)
            #choose randomly amongst all actions
        else:
            m = max(self.q1_table[curr_state])
            l = list()
            print("POSSIBLE ACTIONS: {}".format(possible_actions))
            print("Q table: {}".format(self.q1_table))
            print("curr_state: {}".format(curr_state))
            for x in range(0,len(possible_actions)):
                print("x: {}".format(x))
                if self.q1_table[curr_state][x] == m:
                    l.append(x)
            rnd = random.random()
            y = random.randint(0,len(l)-1)
            a = l[y]
            #########CHANGE ABOVE TO THE FOLLOWING FOR DOUBLE Q-LEARNING#########
            #average actions over q1 and q2
            #choose max from these averages, or if equal max values,
            #then choose randomly among them
        return a
    
    def run(self,agent_host):

        self.prev_s = None
        self.prev_a = None
        tol = 0.01
        current_reward = 0
        total_reward = 0
        
        # wait for a valid observation
        world_state = agent_host.peekWorldState()
        while world_state.is_mission_running and all(e.text=='{}' for e in world_state.observations):
            world_state = agent_host.peekWorldState()
        # wait for a frame to arrive after that
        num_frames_seen = world_state.number_of_video_frames_since_last_state
        while world_state.is_mission_running and world_state.number_of_video_frames_since_last_state == num_frames_seen:
            world_state = agent_host.peekWorldState()
        world_state = agent_host.getWorldState()
        for err in world_state.errors:
            print err

        if not world_state.is_mission_running:
            return 0 # mission already ended
            
        assert len(world_state.video_frames) > 0, 'No video frames!?'
        
        obs = json.loads( world_state.observations[-1].text )
        prev_x = obs[u'XPos']
        prev_y = obs[u'YPos']
        prev_z = obs[u'ZPos']

        #record (for now)
        self.curr_x = obs[u'XPos']
        self.curr_y = obs[u'YPos']
        self.curr_z = obs[u'ZPos']

        total_reward += self.act(world_state,agent_host,current_reward)

        ################################
        require_move = True
        check_expected_position = True
        
        # main loop:
        while world_state.is_mission_running:
        
            # wait for the position to have changed and a reward received
            print 'Waiting for data...',
            while True:
                world_state = agent_host.peekWorldState()
                if not world_state.is_mission_running:
                    print 'mission ended.'
                    break
                if (len(world_state.rewards) > 0 and not all(e.text=='{}' for e in world_state.observations)):
                    obs = json.loads( world_state.observations[-1].text )
                    self.curr_x = obs[u'XPos']
                    self.curr_z = obs[u'ZPos']
                    require_move = False
                    if require_move: 
                        if math.hypot( self.curr_x - prev_x, self.curr_y - prev_y, self.curr_z - prev_z ) > tol:
                            print 'received.'
                            break
                    else:
                        print 'received.'
                        break
                #CHANGE
                #will currently stall here when trying to send 'tp' command due to receiving no rewards
                '''if self.sent_tp:
                    # wait for a valid observation
                    world_state = agent_host.peekWorldState()
                    while world_state.is_mission_running and all(e.text=='{}' for e in world_state.observations):
                        world_state = agent_host.peekWorldState()
                    break;'''
                
            # wait for a frame to arrive after that
            num_frames_seen = world_state.number_of_video_frames_since_last_state
            while world_state.is_mission_running and world_state.number_of_video_frames_since_last_state == num_frames_seen:
                world_state = agent_host.peekWorldState()
                
            num_frames_before_get = len(world_state.video_frames)
            
            world_state = agent_host.getWorldState()
            for err in world_state.errors:
                print err
            current_r = sum(r.getValue() for r in world_state.rewards)
 
            if world_state.is_mission_running:
                assert len(world_state.video_frames) > 0, 'No video frames!?'
                num_frames_after_get = len(world_state.video_frames)
                assert num_frames_after_get >= num_frames_before_get, 'Fewer frames after getWorldState!?'
                frame = world_state.video_frames[-1]
                obs = json.loads( world_state.observations[-1].text )
                self.curr_x = obs[u'XPos']
                self.curr_z = obs[u'ZPos']
                self.curr_y = obs[u'YPos']
                print '\nX, Y, Z:',self.curr_x,',',self.curr_y,',',self.curr_z
                '''print 'New position from observation:',curr_x,',',curr_z,'after action:',self.action[self.prev_a], #NSWE
                if check_expected_position:
                    expected_x = prev_x + [0,0,-1,1][self.prev_a]
                    expected_z = prev_z + [-1,1,0,0][self.prev_a]
                    if math.hypot( curr_x - expected_x, curr_z - expected_z ) > tol:
                        print ' - ERROR DETECTED! Expected:',expected_x,',',expected_z
                        raw_input("Press Enter to continue...")
                    #else:
                    #    print 'as expected.'
                    curr_x_from_render = frame.xPos
                    curr_z_from_render = frame.zPos
                    
                    #print 'New position from render:',curr_x_from_render,',',curr_z_from_render,'after action:',self.actions[self.prev_a], #NSWE
                    if math.hypot( curr_x_from_render - expected_x, curr_z_from_render - expected_z ) > tol:
                        print ' - ERROR DETECTED! Expected:',expected_x,',',expected_z
                        raw_input("Press Enter to continue...")
                    #else:
                        #print 'as expected.'
                else:
                    print'''
                prev_x = self.curr_x
                prev_y = self.curr_y
                prev_z = self.curr_z
                
                # act
                total_reward += self.act(world_state, agent_host, current_reward)
                
        # process final reward
        #self.logger.debug("Final reward: %d" % current_reward)
        total_reward += current_reward

        # update Q values
        if self.training and self.prev_s is not None and self.prev_a is not None:
            old_q = self.q1_table[self.prev_s][self.prev_a]
            self.q1_table[self.prev_s][self.prev_a] = old_q + self.alpha * ( current_r - old_q )
    
        return total_reward
 

def load_grid(world_state):
    """
    Used the agent observation API to get a 21 X 21 grid box around the agent (the agent is in the middle).

    Args
        world_state:    <object>    current agent world state

    Returns
        grid:   <list>  the world grid blocks represented as a list of blocks (see Tutorial.pdf)
    """
    grid = list()
    while world_state.is_mission_running:
        sys.stdout.write(".")
        time.sleep(0.1)
        world_state = agent_host.getWorldState()
        if len(world_state.errors) > 0:
            raise AssertionError('Could not load grid.')

        if world_state.number_of_observations_since_last_state > 0:
            msg = world_state.observations[-1].text
            observations = json.loads(msg)
            grid = observations.get(u'floorAll', 0)
            break
    return grid


######## Create default Malmo objects:  ##############

agent_host = MalmoPython.AgentHost()

#agent_host.addOptionalStringArgument('mission_file',
#    'Path/to/file from which to load the mission.', '../Sample_missions/cliff_walking_1.xml')


try:
    agent_host.parse( sys.argv )
except RuntimeError as e:
    print 'ERROR:',e
    print agent_host.getUsage()
    exit(1)
if agent_host.receivedArgument("help"):
    print agent_host.getUsage()
    exit(0)


num_iterations = 5000
n=1
for episode in range(num_iterations):

    #set up agent
    agent = UnderwaterAgent()
    
    '''mission_file = agent_host.getStringArgument('mission_file')
    with open(mission_file, 'r') as f:
        print "Loading mission from %s" % mission_file
        mission_xml = f.read()'''
    my_mission = MalmoPython.MissionSpec(mission_xml, True)
    my_mission_record = MalmoPython.MissionRecordSpec()
    my_mission.removeAllCommandHandlers()
    my_mission.allowAllDiscreteMovementCommands() 
    my_mission.allowAllAbsoluteMovementCommands() #I'M SO ANNOYED. THIS WAS ALL WE NEEDED. D< !!
    my_mission.requestVideo( 320, 240 )
    my_mission.setViewpoint( 1 )

    cumu_rewards = []
    max_retries = 3
    num_repeats = 150
    for i in range(num_repeats):

        print "\nMap %d - Mission %d of %d:" % ( episode, i+1, num_repeats )
        
        for retry in range(max_retries):
            try:
                agent_host.startMission( my_mission, my_mission_record )
                break
            except RuntimeError as e:
                if retry == max_retries - 1:
                    print "Error starting mission:",e
                    exit(1)
                else:
                    time.sleep(2)

        # Loop until mission starts:
        print "Waiting for new mission to start ... ",

        world_state = agent_host.getWorldState()
        while not world_state.has_mission_begun:
            sys.stdout.write(".")
            time.sleep(0.1)
            world_state = agent_host.getWorldState()
            for error in world_state.errors:
                print "Error:",error.text

        cumu_reward = agent.run(agent_host)
        cumu_rewards += [cumu_reward]

        #---clean up---
        time.sleep(0.5)

    print
    print "Mission ended"

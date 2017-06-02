import MalmoPython
import os
import sys
import time
import json
import random
import math
from timeit import default_timer as timer

saved_filename = "/Users/andrewdo/Desktop/Malmo-0.21.0-Mac-64bit/Sample_missions/WaterWorldFloor2"
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
                <AgentQuitFromTouchingBlockType>
                    <Block type="redstone_block"/>
                </AgentQuitFromTouchingBlockType>
                <ObservationFromFullStats/>
                <AbsoluteMovementCommands/>
                <DiscreteMovementCommands/>
                <MissionQuitCommands/>
                <RewardForCollectingItem>
                    <Item reward="10.0"  type="ender_pearl"></Item>
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
        self.sent_tp_down = False
        self.training = True


    def teleport(self, agent_host, move_up):
        """Directly teleport to a specific position."""

        move_by = 4
        if move_up:
            tel_y= self.curr_y+move_by 
        else:
            tel_y= self.curr_y-move_by 
        tp_command = "tp {} {} {}".format(self.curr_x,tel_y,self.curr_z)
        return tp_command
        

    def get_possible_actions(self, world_state,agent_host):
        """Returns all possible actions that can be done at the current state. """
        action_list = []
        possibilities = {'movenorth 1': -3,'movesouth 1': 3,'moveeast 1': 1,'movewest 1': -1}
        
        check = world_state.observations
        #this problem occurs because we are trying to access world_state.observations[-1].text
        #when theres nothing there so the current work around 
        #keep checking until observations is not empty
        while not len(check):
            check = world_state.observations

        #if we are here then the check has return not empty
        #grab whatever obs we see
        obs_text = world_state.observations[-1].text

        obs = json.loads(obs_text)
        grid = load_grid(world_state)

        #adding in some constraints in case agent dies in the middle of grabbing actions
        while grid==[] and obs[u'Life']>0 and obs[u'IsAlive'] and world_state.is_mission_running:
            print("alive but somehow grid is empty??")
            world_state = agent_host.getWorldState() #this should fix it?
            if world_state.number_of_observations_since_last_state > 0:
                obs_text = world_state.observations[-1].text
                obs = json.loads(obs_text)
                grid = load_grid(world_state)
        if obs[u'Life']<0 or not obs[u'IsAlive'] or not world_state.is_mission_running:
            agent_host.sendCommand("quit")

        if obs[u'Life']>0 and obs[u'IsAlive']:
            for k,v in possibilities.items():
                #with current grid, index 31 will always be our agent's current location
                #check walls to see whether can move left,right,back,forward
                try:
                    if grid[31+v+9] == 'water' or grid[31+v+9] == 'wooden_door': #+9 because we want to check
                        action_list.append(k)                                    #where our feet are located
                except Exception as ex:
                    print '**********', len(grid)
                    print '**********', (31 + v + 9)
                    raise ex
            #check if you can teleport down a level       
            if grid[31-27] == 'water' or grid[31-27] == 'wooden_door':
                action_list.append(self.teleport(agent_host,False))
                time.sleep(0.5)
            #check if you can teleport up a level
            if grid[31+45] == 'water' or grid[31+45] == 'wooden_door':
                action_list.append(self.teleport(agent_host,True))
                time.sleep(0.5)
        else:
            action_list.append("quit")
        return action_list

    def act(self,world_state,agent_host,current_reward):
        
        obs_text = world_state.observations[-1].text
        obs = json.loads(obs_text)

        current_air = obs[u'Air']
        if current_air>=0 and current_air<=100:
            air_state = 'low'
        elif current_air>100 and current_air<=200:
            air_state = 'medium'
        else: #current_air>200
            air_state = 'high'
            
        curr_state = "%d.%d.%d.%s" % (int(obs[u'XPos']),int(obs[u'YPos']), int(obs[u'ZPos']),air_state)

    
        poss_act = self.get_possible_actions(world_state,agent_host)
        #making sure that curr_state!=prev_state... agent should always be moving/taking some action each step
        curr_list=0
        prev_list=1
        if self.prev_s!=None:
            cs = curr_state.split(".");
            ps = self.prev_s.split(".");
            curr_list = [cs[0],cs[1],cs[2]]
            prev_list = [ps[0],ps[1],ps[2]]
        while curr_list==prev_list and world_state.is_mission_running:
            # print "\nError: prev state == curr state"
            world_state = agent_host.getWorldState() #this should fix it?
            if world_state.number_of_observations_since_last_state > 0:
                obs_text = world_state.observations[-1].text
                obs = json.loads(obs_text)
                current_air = obs[u'Air']
                if current_air>=0 and current_air<=100:
                    air_state = 'low'
                elif current_air>100 and current_air<=200:
                    air_state = 'medium'
                else: #current_air>200
                    air_state = 'high'
                curr_state = "%d.%d.%d.%s" % (int(obs[u'XPos']),int(obs[u'YPos']), int(obs[u'ZPos']),air_state)
                cs = curr_state.split(".");
                curr_list = [cs[0],cs[1],cs[2]]
        if not world_state.is_mission_running:
            agent_host.sendCommand("quit")
                
        #update both if action doesn't exist in one.. (so they always exist in both)
        if curr_state not in self.q1_table:
            self.q1_table[curr_state] = ([0] * len(self.get_possible_actions(world_state,agent_host)))
            self.q2_table[curr_state] = ([0] * len(self.get_possible_actions(world_state,agent_host)))


        # update Q values
        if self.training and self.prev_s is not None and self.prev_a is not None:
            old_q_1 = self.q1_table[self.prev_s][self.prev_a]
            old_q_2 = self.q2_table[self.prev_s][self.prev_a]
            
            #with probability 50% update q1_table else update q2_table
            if random.random() < 0.5:
                #print 'waffles'
                #update first q_table
                self.q1_table[self.prev_s][self.prev_a] = \
                 old_q_1 + self.alpha * (current_reward + self.gamma * self.q2_table[curr_state][self.q1_table[curr_state].index(max(self.q1_table[curr_state]))] - old_q_1)
                print 'curr state: {}'.format(curr_state)
                print '\nq1 old: {}'.format(old_q_1)
                print 'q1 new: {}'.format(self.q1_table[self.prev_s][self.prev_a])
            else:
                #print 'pancakes'
                #update second q_table
                self.q2_table[self.prev_s][self.prev_a] = \
                old_q_2 + self.alpha * (current_reward + self.gamma * self.q1_table[curr_state][self.q2_table[curr_state].index(max(self.q2_table[curr_state]))] - old_q_2)
                print 'curr state: {}'.format(curr_state)
                print '\nq2 old: {}'.format(old_q_2)
                print 'q2 new: {}'.format(self.q2_table[self.prev_s][self.prev_a])

        #select next action
        possible_actions = self.get_possible_actions(world_state,agent_host)
        a = self.choose_action(curr_state,possible_actions)

        #send selected action
        print("\n--TOOK ACTION: {}".format(possible_actions[a]))
        
        if possible_actions[a].find("tp")!=-1:
            new_s = possible_actions[a].split(" ")
            old_s = curr_state.split(".")
            if new_s[2]<old_s[1]:
                self.sent_tp_down = True
        agent_host.sendCommand(possible_actions[a])
        self.prev_s = curr_state
        self.prev_a = a
        
        return current_reward
                
    
    def choose_action(self,curr_state,possible_actions):

        rnd = random.random()
        if rnd < self.epsilon:
            #choose randomly amongst all actions
            rnd = random.random()
            a = random.randint(0,len(possible_actions) - 1)
        else:
            # average over the values of both the q tables and take the maximum among them
            q_3 = list()
            print 'length: ', len(possible_actions)
            print 'q1_length: ',len(self.q1_table[curr_state])
            print 'q2_length: ',len(self.q2_table[curr_state])
            print 'actions: ', possible_actions
            print 'cs: ', curr_state

            for action in range(len(possible_actions)):
                equation = (self.q1_table[curr_state][action] + self.q2_table[curr_state][action]) / 2
                q_3.append(equation)

            # take the maximum in the current state of the newly created table_3
            max_value = max(q_3)
            list_of_max_actions = list()
            for x in range(len(possible_actions)):
                if q_3[x] == max_value:
                    list_of_max_actions.append(x)

            y = random.randint(0, len(list_of_max_actions)-1)
            a = list_of_max_actions[y]
        return a

    def compute_air_reward(self,current_air):
        reward = 0
        if current_air>=0 and current_air<=100:
            reward = 10
        elif current_air>100 and current_air<=200:
            reward = 5
        else: # means 300>=current_air>200
            reward = -1
        return reward
    
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
                    self.curr_y = obs[u'YPos']
                    self.curr_z = obs[u'ZPos']
                    require_move = False
                    if require_move: 
                        if math.hypot( self.curr_x - prev_x, self.curr_y - prev_y, self.curr_z - prev_z ) > tol:
                            print 'received.'
                            break
                    else:
                        print 'received.'
                        break
                
            # wait for a frame to arrive after that
            num_frames_seen = world_state.number_of_video_frames_since_last_state
            while world_state.is_mission_running and world_state.number_of_video_frames_since_last_state == num_frames_seen:
                world_state = agent_host.peekWorldState()

            num_frames_before_get = len(world_state.video_frames)
            
            world_state = agent_host.getWorldState()
            for err in world_state.errors:
                print err

            #grab grid and figure out if standing in water/air
            grid = load_grid(world_state)
            while grid==[] and world_state.is_mission_running and obs[u'Life']>0 and obs[u'IsAlive']:
                print("alive but somehow grid is empty??----2!")
                world_state = agent_host.getWorldState() #this should fix it?
                if world_state.number_of_observations_since_last_state > 0:
                    obs_text = world_state.observations[-1].text
                    obs = json.loads(obs_text)
                    grid = load_grid(world_state)
                if not obs[u'IsAlive'] or obs[u'Life']==0:
                    agent_host.sendCommand("quit")

                
            if world_state.is_mission_running:
                air_reward = 0
                if grid[31+9] == 'wooden_door':
                    air_reward = self.compute_air_reward(obs[u'Air'])
                    print("--GAVE REWARD FOR AIR: {}--".format(air_reward))
                    print('current_reward -before air-: {}'.format(sum(r.getValue() for r in world_state.rewards)))
                    print('current_reward -after air-: {}'.format(sum(r.getValue() for r in world_state.rewards)+air_reward))

                tp_down_reward = 0
                if self.sent_tp_down:
                    tp_down_reward = 1
                    self.sent_tp_down = False
                    print("--GAVE REWARD FOR TRANSPORTING DOWN: {}--".format(tp_down_reward))
                    print('current_reward -before tp_down-: {}'.format(sum(r.getValue() for r in world_state.rewards)))
                    print('current_reward -after tp_down-: {}'.format(sum(r.getValue() for r in world_state.rewards)+air_reward+tp_down_reward))

                #compute the current_reward (which includes additional award for finding air or moving down)
                current_reward = sum(r.getValue() for r in world_state.rewards)+air_reward+tp_down_reward
                
 
            if world_state.is_mission_running:
                assert len(world_state.video_frames) > 0, 'No video frames!?'
                num_frames_after_get = len(world_state.video_frames)
                assert num_frames_after_get >= num_frames_before_get, 'Fewer frames after getWorldState!?'
                frame = world_state.video_frames[-1]
                obs = json.loads( world_state.observations[-1].text )
                self.curr_x = obs[u'XPos']
                self.curr_z = obs[u'ZPos']
                self.curr_y = obs[u'YPos']
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
        total_reward += current_reward

        # update Q values
        if self.training and self.prev_s is not None and self.prev_a is not None:
            old_q_1 = self.q1_table[self.prev_s][self.prev_a]
            old_q_2 = self.q2_table[self.prev_s][self.prev_a]

            self.q1_table[self.prev_s][self.prev_a] = old_q_1 + self.alpha * (current_reward - old_q_1)
            self.q2_table[self.prev_s][self.prev_a] = old_q_2 + self.alpha * (current_reward - old_q_2)
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
    num_tries = 5
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
            if len(grid) == 0:
                print 'SOMETHING IS SOOOO WRONG!!!!'
                num_tries -= 1

                if num_tries < 0:
                    raise AssertionError('OH NO!!! TOO MANY TRIES')
                continue

            if num_tries < 5:
                raise AssertionError('******** ITS THE GOOD KIND OF ERROR')
            break

    return grid


######## Create default Malmo objects:  ##############
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately
agent_host = MalmoPython.AgentHost()

#agent_host.addOptionalStringArgument('mission_file',
#    'Path/to/file from which to load the mission.', '../Sample_missions/cliff_walking_1.xml')
agent_host.addOptionalFloatArgument('alpha',
    'Learning rate of the Q-learning agent.', 0.1)
agent_host.addOptionalFloatArgument('epsilon',
    'Exploration rate of the Q-learning agent.', 0.01)
agent_host.addOptionalFloatArgument('gamma', 'Discount factor.', 1.0)
agent_host.addOptionalFlag('load_model', 'Load initial model from model_file.')
agent_host.addOptionalStringArgument('model_file', 'Path to the initial model file', '')
agent_host.addOptionalFlag('debug', 'Turn on debugging.')

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
    my_mission.allowAllAbsoluteMovementCommands() 
    my_mission.requestVideo( 320, 240 )
    my_mission.setViewpoint( 1 )

    my_clients = MalmoPython.ClientPool()
    my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000)) # add Minecraft machines here as available

    cumu_rewards = []
    max_retries = 3
    num_repeats = 150
    agentID = 0
    expID = 'project'
    
    for i in range(num_repeats):

        print "\nMap %d - Mission %d of %d:" % ( episode, i+1, num_repeats )

        my_mission_record = MalmoPython.MissionRecordSpec( "./save_%s-map%d-rep%d.tgz" % (expID, episode, i) )
        my_mission_record.recordCommands()
        my_mission_record.recordMP4(20, 400000)
        my_mission_record.recordRewards()
        my_mission_record.recordObservations()
        
        for retry in range(max_retries):
            try:
                agent_host.startMission( my_mission, my_clients, my_mission_record, agentID, "%s-%d" % (expID, i) )
                break
            except RuntimeError as e:
                if retry == max_retries - 1:
                    print "Error starting mission:",e
                    exit(1)
                else:
                    time.sleep(2)

        # Loop until mission starts:
        print "Waiting for new mission to start .............. ",

        world_state = agent_host.getWorldState()
        while not world_state.has_mission_begun:
            sys.stdout.write(".")
            time.sleep(0.1)
            world_state = agent_host.getWorldState()
            for error in world_state.errors:
                print "Error:",error.text

        cumu_reward = agent.run(agent_host)
        print("REWARD FOR MISSION {}: {}".format(episode,cumu_reward))
        cumu_rewards += [cumu_reward]

        #creates a file and writes reward for each respective mission that ran 
        with open("rewards.txt", "a") as myfile:
            myfile.write("\nREWARD FOR MISSION {}: {}".format(i,cumu_reward))

        #---clean up---
        time.sleep(1)

    print
    print "Mission ended"


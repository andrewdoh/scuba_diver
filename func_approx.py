import MalmoPython
import os
import sys
import time
import json
import random
import math
from timeit import default_timer as timer

saved_filename = "C:\Users\Caitlin\Desktop\CS175-PROJECT\Sideways_3Floors"
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
                <ObservationFromDistance> 
                    <Marker name="Goal" x="1155.5" y="25" z="-478.5"/>
                </ObservationFromDistance>
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
                        <min x="-5" y="0" z="-1"/>
                        <max x="5" y="0" z="1"/>
                    </Grid>
                </ObservationFromGrid>
            </AgentHandlers>
        </AgentSection>
    </Mission>'''


class UnderwaterAgent(object):
    def __init__(self, alpha=.9, gamma=.3, n=1):
        self.epsilon = 0.1
        self.q1_table = {}  # value of state
        self.q2_table = {}  # value of advantage/action
        self.n, self.alpha, self.gamma = n, alpha, gamma

        self.prev_x = None
        self.prev_y = None
        self.prev_z = None

        self.curr_x = None
        self.curr_y = None
        self.curr_z = None
        
        self.sent_tp_down = False
        self.training = True
        
        self.air_reward = 0
        self.is_air_next = False
        self.action_for_air = 0

        self.time_alive = 0

        self.start_point = "1142.25.-481" 
        self.goal_point = "1155.25.-478"
        self.floor_side_length = 4 #floors will always have squared  

    def dir_from_goal(self,old_curr_state):
        s = old_curr_state.split(".")
        g = self.goal_point.split(".")
        s_x = int(s[0])
        s_z = int(s[2])
        g_x = int(g[0])
        g_z = int(g[2])

        direction = 'Goal' #only other possible state is the goal itself
        if abs(g_z-s_z) > abs(g_x-s_x):
            #should be N/S only
            if g_z>s_z:
                direction = 'S'
            else:
                direction = 'N'
        else:
            #should be W/E only
            if g_x>s_x:
                direction = 'E'
            else:
                direction = 'W'

        #assuming agent always starts in right-most corner of top floor
        start = self.start_point.split(".")
        floor_num = s_x-int(start[0])
        if floor_num >= (self.floor_side_length+1):
            while floor_num%(self.floor_side_length+1) != 0:
                floor_num-=1
            floor_num = (floor_num/(self.floor_side_length+1))+1
        else:
            floor_num = 1
        direction+= '%d' % floor_num

        if floor_num!=1 and floor_num!=2 and floor_num!=3:
            print'-------------------------ERROR!!!'

        '''1-3 1/4=0,2/4=0,3/4=0
        5-8 5/4=1,6/4=1,7/4=1,8/4=2
        10-13 10/4=2,11/4=2,12/4=3,13/4=3
        15-18 15/4=3,16/4=4,17/4=4,18/4=4
        20-23 20/4=5,...'''
             
        return direction
                

    def teleport(self, agent_host, move_up):
        """Directly teleport to a specific position."""
        
        move_by = 5 #equal to how many hops we need to take to reach new floor
        if move_up:
            #teleport up
            tel_x = self.curr_x - move_by
        else:
            #teleport down
            tel_x = self.curr_x + move_by
        tp_command = "tp {} {} {}".format(tel_x, self.curr_y, self.curr_z)
        print "original state: {} {} {}".format(self.curr_x, self.curr_y, self.curr_z)
        print 'sent command: {} {} {}'.format(tel_x, self.curr_y, self.curr_z)
        return tp_command

    def get_possible_actions(self, world_state, agent_host):
        """Returns all possible actions that can be done at the current state. """
        action_list = []
        #note: agent starts out facing south
        possibilities = {'movenorth 1': -11, 'movesouth 1': 11, 'moveeast 1': 1, 'movewest 1': -1}

        grid = load_grid(world_state)
        world_state = agent_host.getWorldState()
        if not world_state.is_mission_running:
            if len(grid) == 0:
                print '**** Moshe was right'
            else:
                print '**** Still dies, but at least grid is not empty'
            raise NotImplementedError('Not really :) We just died')

        for k, v in possibilities.items():
            # with current grid, index 16 will always be our agent's current location
            # check walls to see whether can move left,right,back,forward
            try:
                if grid[16 + v] == 'water' or grid[16 + v] == 'wooden_door':  # +9 because we want to check
                    action_list.append(k)  # where our feet are located
                    #check for redstone block
                    if grid[16+v] == 'wooden_door':
                        self.is_air_next = True
                        self.action_for_air = k
                    
            except Exception as ex:
                print '**********', len(grid)
                print '**********', (16+v)
                raise ex
            
        # check if you can teleport down a level (equivalent to hopping 5 spaces to the left)
        if grid[16+5] == 'water' or grid[16+5] == 'wooden_door':
            action_list.append('tp_down')
            #check for redstone_block
            if grid[16+5] == 'wooden_door':
                self.is_air_next = True
                self.action_for_air = self.teleport(agent_host, False)
            # time.sleep(0.1)
        # check if you can teleport up a level (equivalent to hopping 5 spaces to the right)
        if grid[16-5] == 'water' or grid[16-5] == 'wooden_door':
            action_list.append('tp_up')
            #check for redstone_block
            if grid[16-5] == 'wooden_door':
                self.is_air_next = True
                self.action_for_air = self.teleport(agent_host, True)
        
        return action_list

    def act(self, world_state, agent_host, current_reward):

        obs_text = world_state.observations[-1].text
        obs = json.loads(obs_text)

        current_air = obs[u'Air']
        if current_air >= 0 and current_air <= 100:
            air_state = 'low'
        elif current_air > 100 and current_air <= 200:
            air_state = 'medium'
        else:  # current_air>200
            air_state = 'high'

        #curr_state = "%d.%d.%d.%s" % (int(obs[u'XPos']), int(obs[u'YPos']), int(obs[u'ZPos']), air_state)
            
        #keeping old state to make sure we take another step with each new action
        old_curr_state = "%d.%d.%d.%s" % (int(obs[u'XPos']), int(obs[u'YPos']), int(obs[u'ZPos']), air_state)
        self.curr_x = obs[u'XPos']
        self.curr_y = obs[u'YPos']
        self.curr_z = obs[u'ZPos']
        print("\ncurr_state: {}".format(old_curr_state))
        #reducing states by euclid dist + direction of goal in relation to the agent + current amount of air
        direction = self.dir_from_goal(old_curr_state)
        curr_state = "%d.%s.%s" % (int(obs[u'distanceFromGoal']),direction,air_state)

        # poss_act = self.get_possible_actions(world_state, agent_host)
        # time.sleep(0.1)
        # making sure that curr_state!=prev_state... agent should always be moving/taking some action each step
        curr_list = 0
        prev_list = 1
        if self.old_prev_s != None:
            cs = old_curr_state.split(".")
            ps = self.old_prev_s.split(".")
            curr_list = [cs[0], cs[1], cs[2]]
            prev_list = [ps[0], ps[1], ps[2]]
        while curr_list == prev_list and world_state.is_mission_running:
            print "\n--------------------------------Error: prev state == curr state"
            world_state = agent_host.getWorldState()  # this should fix it?
            if world_state.number_of_observations_since_last_state > 0:
                obs_text = world_state.observations[-1].text
                obs = json.loads(obs_text)
                current_air = obs[u'Air']
                if current_air >= 0 and current_air <= 100:
                    air_state = 'low'
                elif current_air > 100 and current_air <= 200:
                    air_state = 'medium'
                else:  # current_air>200
                    air_state = 'high'
                #curr_state = "%d.%d.%d.%s" % (int(obs[u'XPos']), int(obs[u'YPos']), int(obs[u'ZPos']), air_state)
                old_curr_state = "%d.%d.%d.%s" % (int(obs[u'XPos']), int(obs[u'YPos']), int(obs[u'ZPos']), air_state)
                self.curr_x = obs[u'XPos']
                self.curr_y = obs[u'YPos']
                self.curr_z = obs[u'ZPos']
                direction = self.dir_from_goal(old_curr_state)
                curr_state = "%d.%s.%s" % (int(obs[u'distanceFromGoal']),direction,air_state)
                cs = old_curr_state.split(".");
                curr_list = [cs[0], cs[1], cs[2]]
        print("curr_state_new?: {}".format(old_curr_state))
        if not world_state.is_mission_running:
            agent_host.sendCommand("quit")

        # pre-initialize each state with every possible action
        # (we may have walls that obstruct certain actions, but the agent may have the same state in a different
        # location. But we must reduce state space and not take every location into account.
        possible_actions = self.get_possible_actions(world_state, agent_host)
        
        if curr_state not in self.q1_table:
            self.q1_table[curr_state] = {}
            self.q2_table[curr_state] = {}
            for i in ['movenorth 1','movesouth 1','moveeast 1','movewest 1','tp_down','tp_up']:
                self.q1_table[curr_state][i] = 0
                self.q2_table[curr_state][i] = 0

        # update Q values
        if self.training and self.prev_s is not None and self.prev_a is not None:
            try:
                old_q_1 = self.q1_table[self.prev_s][self.prev_a]
                old_q_2 = self.q2_table[self.prev_s][self.prev_a]
            except Exception as e:
                print self.prev_a, self.old_prev_s
                print curr_state
                raise AssertionError('BAD BAD BAD BAD ******* FIND OUT WHY!!!')

            act = {}
            # with probability 50% update q1_table else update q2_table
            if random.random() < 0.5:
                # update first q_table    
                for a in possible_actions:
                    act[a] = self.q1_table[curr_state][a]
                max_act = max(act.keys(), key=(lambda k: act[k])) #will return first if all equal?
                #print '---q1_max_act: ',max_act                   #should we make this random if all equal??? CHANGE
                #print self.q1_table[curr_state][max_act]
                
                self.q1_table[self.prev_s][self.prev_a] = \
                    old_q_1 + self.alpha * (current_reward + self.gamma * self.q2_table[curr_state][
                        max_act] - old_q_1)
                '''print 'curr state: {}'.format(curr_state)
                print '\nq1 old: {}'.format(old_q_1)
                print 'q1 new: {}'.format(self.q1_table[self.prev_s][self.prev_a])'''
            else:
                # update second q_table
                for a in possible_actions:
                    act[a] = self.q2_table[curr_state][a]
                max_act = max(act.keys(), key=(lambda k: act[k])) #same here CHANGE
                #print '---q2_max_act: ',max_act
                #print self.q2_table[curr_state][max_act]
                                            
                self.q2_table[self.prev_s][self.prev_a] = \
                    old_q_2 + self.alpha * (current_reward + self.gamma * self.q1_table[curr_state][
                        max_act] - old_q_2)

                '''print '\nq2 old: {}'.format(old_q_2)
                print 'q2 new: {}'.format(self.q2_table[self.prev_s][self.prev_a])'''

        # select next action
        a = self.choose_action(curr_state, possible_actions)

        if self.is_air_next:
            if possible_actions[a]==self.action_for_air:
                self.air_reward = self.compute_air_reward(current_air)
            self.is_air_next = False;

        # send selected action
        print("--TOOK ACTION: {}".format(possible_actions[a]))

        command_to_send = possible_actions[a]
        #if command to send is a transport, then calculate the coordinates to send it to
        if possible_actions[a]=="tp_down":
                self.sent_tp_down = True
        if possible_actions[a].find("tp")!=-1:
            if self.sent_tp_down:
                command_to_send = self.teleport(agent_host, False)
            else:
                command_to_send = self.teleport(agent_host, True)
        
        agent_host.sendCommand(command_to_send)
        time.sleep(0.25)

        self.prev_s = curr_state
        self.old_prev_s = old_curr_state
        self.prev_a = possible_actions[a]

        return current_reward

    def choose_action(self, curr_state, possible_actions):

        rnd = random.random()
        if rnd < self.epsilon:
            # choose randomly amongst all actions
            rnd = random.random()
            a = random.randint(0, len(possible_actions) - 1)
        else:
            # average over the values of both the q tables and take the maximum among them
            q_3 = list()
            '''print 'length: ', len(possible_actions)
            print 'q1_length: ', len(self.q1_table[curr_state])
            print 'q2_length: ', len(self.q2_table[curr_state])'''
            print 'actions: ', possible_actions
            print 'cs: ', curr_state
            '''print 'q1: ', self.q1_table[curr_state]
            print 'q2: ', self.q2_table[curr_state]
            print 'prev state:', self.prev_s'''
            #only average out of the possible actions for the current state (i.e. we don't want to pick
            #an action that will make us move into a wall)
            for action in possible_actions:
                equation = (self.q1_table[curr_state][action] + self.q2_table[curr_state][action]) / 2
                q_3.append(equation)

            # take the maximum in the current state of the newly created table_3
            max_value = max(q_3)
            list_of_max_actions = list()
            for x in range(len(q_3)):
                if q_3[x] == max_value:
                    list_of_max_actions.append(x)

            y = random.randint(0, len(list_of_max_actions) - 1)
            a = list_of_max_actions[y]
        return a

    def compute_air_reward(self, current_air):
        reward = 0
        if current_air >= 0 and current_air <= 100:
            reward = 10
        elif current_air > 100 and current_air <= 200:
            reward = 5
        else:  # means 300>=current_air>200
            reward = -1
        return reward

    def run(self, agent_host):

        #sets camera angle to top-down view
        agent_host.sendCommand("setPitch 100")

        self.old_prev_s = None
        self.prev_s = None
        self.prev_a = None
        tol = 0.01
        current_reward = 0
        total_reward = 0

        # wait for a valid observation
        time.sleep(0.1)
        world_state = agent_host.peekWorldState()
        # len()<2 because may only return distance to goal observation
        while world_state.is_mission_running and len(world_state.observations)<2 and all(e.text == '{}' for e in world_state.observations):
            world_state = agent_host.peekWorldState()
        # wait for a frame to arrive after that
        num_frames_seen = world_state.number_of_video_frames_since_last_state
        while world_state.is_mission_running and world_state.number_of_video_frames_since_last_state == num_frames_seen:
            world_state = agent_host.peekWorldState()
        world_state = agent_host.getWorldState()
        for err in world_state.errors:
            print err

        if not world_state.is_mission_running:
            return 0  # mission already ended

        assert len(world_state.video_frames) > 0, 'No video frames!?'

        obs = json.loads(world_state.observations[-1].text)
        try:
            self.prev_x = obs[u'XPos']
            self.prev_y = obs[u'YPos']
            self.prev_z = obs[u'ZPos']
        except KeyError:
            print '-------',len(world_state.observations)
            raise exception

        try:
            #----------------------------call act-----------------------------------#
            total_reward += self.act(world_state, agent_host, current_reward)
        except NotImplementedError as bullshit:
            # We actually died but this is how we catch it now (CHANGE IT!!!!!)
            return total_reward

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
                if (len(world_state.rewards) > 0 and not all(e.text == '{}' for e in world_state.observations)):
                    obs = json.loads(world_state.observations[-1].text)
                    self.curr_x = obs[u'XPos']
                    self.curr_y = obs[u'YPos']
                    self.curr_z = obs[u'ZPos']
                    self.time_alive = obs[u'TimeAlive']
                    
                    require_move = False
                    if require_move:
                        if math.hypot(self.curr_x - self.prev_x, self.curr_y - self.prev_y, self.curr_z - self.prev_z) > tol:
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

            # per moshe recommendation if grid returns empty we want to exit gracefully so return None
            grid = load_grid(world_state)
            air_reward = 0
            tp_down_reward = 0
            if grid and world_state.is_mission_running:
                if self.air_reward != 0:
                    air_reward = self.air_reward
                    self.air_reward = 0
                    '''print("--------------GAVE REWARD FOR AIR: {}".format(air_reward))
                    print('current_reward -before air-: {}'.format(sum(r.getValue() for r in world_state.rewards)))
                    print('current_reward -after air-: {}'.format(
                        sum(r.getValue() for r in world_state.rewards) + air_reward))'''

                if self.sent_tp_down:
                    tp_down_reward = 1
                    self.sent_tp_down = False
                    '''print("--GAVE REWARD FOR TRANSPORTING DOWN: {}".format(tp_down_reward))
                    print('current_reward -before tp_down-: {}'.format(sum(r.getValue() for r in world_state.rewards)))
                    print('current_reward -after tp_down-: {}'.format(
                        sum(r.getValue() for r in world_state.rewards) + air_reward + tp_down_reward))'''

                # compute the current_reward (which includes additional award for finding air or moving down)
                current_reward = sum(r.getValue() for r in world_state.rewards) + air_reward + tp_down_reward
            else:
                print("\nBREAKING LOOP. EXITING.\nBREAKING LOOP. EXITING.\nBREAKING LOOP. EXITING.")
                current_reward = sum(r.getValue() for r in world_state.rewards) + air_reward + tp_down_reward
                break;

            if world_state.is_mission_running:
                assert len(world_state.video_frames) > 0, 'No video frames!?'
                num_frames_after_get = len(world_state.video_frames)
                assert num_frames_after_get >= num_frames_before_get, 'Fewer frames after getWorldState!?'
                frame = world_state.video_frames[-1]
                obs = json.loads(world_state.observations[-1].text)
                self.curr_x = obs[u'XPos']
                self.curr_z = obs[u'ZPos']
                self.curr_y = obs[u'YPos']

                self.prev_x = self.curr_x
                self.prev_y = self.curr_y
                self.prev_z = self.curr_z

                # act
                try:
                    total_reward += self.act(world_state, agent_host, current_reward)
                except NotImplementedError as ex:
                    print 'FIX THIS!!!!'
                    return total_reward

        # process final reward
        total_reward += current_reward

        # update Q values
        if self.training and self.old_prev_s is not None and self.prev_a is not None:
            old_q_1 = self.q1_table[self.prev_s][self.prev_a]
            old_q_2 = self.q2_table[self.prev_s][self.prev_a]

            self.q1_table[self.prev_s][self.prev_a] = old_q_1 + self.alpha * (current_reward - old_q_1)
            self.q2_table[self.prev_s][self.prev_a] = old_q_2 + self.alpha * (current_reward - old_q_2)
        return total_reward


def load_grid(world_state):
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

agent_host.addOptionalFlag('load_model', 'Load initial model from model_file.')
agent_host.addOptionalStringArgument('model_file', 'Path to the initial model file', '')
agent_host.addOptionalFlag('debug', 'Turn on debugging.')

try:
    agent_host.parse(sys.argv)
except RuntimeError as e:
    print 'ERROR:', e
    print agent_host.getUsage()
    exit(1)
if agent_host.receivedArgument("help"):
    print agent_host.getUsage()
    exit(0)
    

# set up agent
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
my_mission.requestVideo(320, 240)
my_mission.setViewpoint(1)

my_clients = MalmoPython.ClientPool()
my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000))  # add Minecraft machines here as available

end_trials = False
cumu_rewards = []
max_retries = 3
num_repeats = 1000
agentID = 0
expID = 'project'

for i in range(num_repeats):

    print "\nEpisode %d of %d:" % (i + 1, num_repeats)

    my_mission_record = MalmoPython.MissionRecordSpec("./save_%s-ep%d.tgz" % (expID, i))
    my_mission_record.recordCommands()
    my_mission_record.recordMP4(20, 400000)
    my_mission_record.recordRewards()
    my_mission_record.recordObservations()

    for retry in range(max_retries):
        try:
            agent_host.startMission(my_mission, my_clients, my_mission_record, agentID, "%s-%d" % (expID, i))
            break
        except RuntimeError as e:
            if retry == max_retries - 1:
                print "Error starting mission:", e
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
            print "Error:", error.text



    cumu_reward = agent.run(agent_host)

    if (i + 1)%5 == 0:
        if cumu_reward == 97: #best solution for 4x4 3-floor map
            end_trials = True
            print 'Found Solution'
            print 'Done'
    
    if cumu_reward is not None:
        print("REWARD FOR MISSION {}: {}".format(i, cumu_reward))
        cumu_rewards += [cumu_reward]
    else:
        print("grid was empty skipped episode")

    # creates a file and writes reward for each respective mission that ran
    with open("rewards_alpha9_gamma3_eps1_funcapprox_NESWonly.txt", "a") as myfile:
        if cumu_reward is not None:
            myfile.write("REWARD FOR MISSION {}: {}\n".format(i, cumu_reward))
        else:
            myfile.write("grid was empty skipped episode {}.\n".format(i))
    with open("timeAlive_alpha9_gamma3_eps1_funcapprox_NESWonly.txt", "a") as myfile:
        if cumu_reward is not None:
            #subtracting time alive by 100000 because 100000 is the count down time. Time alive is
            #how much of that is left by the time the episode terminates. Represented in milliseconds.
            myfile.write("TIME ALIVE FOR MISSION {}: {}\n".format(i, 100000-agent.time_alive))
        else:
            myfile.write("grid was empty skipped episode {}.\n".format(i))
            
    if end_trials:
        break;

    # ---clean up---
    time.sleep(1)

print
print "Mission ended"


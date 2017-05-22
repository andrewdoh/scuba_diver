# ------------------------------------------------------------------------------------------------
# Copyright (c) 2016 Microsoft Corporation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ------------------------------------------------------------------------------------------------

# The "Cliff Walking" example using Q-learning.
# From pages 148-150 of:
# Richard S. Sutton and Andrews G. Barto
# Reinforcement Learning, An Introduction
# MIT Press, 1998

import MalmoPython
import json
import logging
import math
import os
import random
import sys
import time
#import Tkinter as tk

save_images = False
if save_images:
    from PIL import Image

class TabQAgent:
    """Tabular Q-learning agent for discrete state/action spaces."""

    def __init__(self, actions=[], epsilon=0.1, alpha=0.1, gamma=1.0, debug=False, canvas=None, root=None):
        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma
        self.training = True

        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        self.logger.handlers = []
        self.logger.addHandler(logging.StreamHandler(sys.stdout))

        self.actions = actions
        self.q_table_1 = {}
        self.q_table_2 = {}
        self.q_table_3 = {}
        #self.canvas = canvas
        self.root = root

        self.rep = 0

    def loadModel(self, model_file):
        """load q table from model_file"""
        with open(model_file) as f:
            self.q_table = json.load(f)

    def training(self):
        """switch to training mode"""
        self.training = True


    def evaluate(self):
        """switch to evaluation mode (no training)"""
        self.training = False

    def load_grid(self, world_state):
        """
        Used the agent observation API to get a 21 X 21 grid box around the agent (the agent is in the middle).
        Args

        world_state:    <object>    current agent world state

        Returns

        grid:   <list>  the world grid blocks represented as a list of blocks (see Tutorial.pdf)
        """
        while world_state.is_mission_running:
            #sys.stdout.write(".")
            time.sleep(0.1)
            world_state = agent_host.getWorldState()
            if len(world_state.errors) > 0:
                raise AssertionError('Could not load grid.')
            # for error in world_state.errors:
            #     print "Error:",error.text
            if world_state.number_of_observations_since_last_state > 0:
                msg = world_state.observations[-1].text
                observations = json.loads(msg)
                grid = observations.get(u'aroundagent3x2x3', 0)
                break

        return grid


    def get_possible_actions(self, world_state, current_s):

        action_list = []
        #to determine possible action needs a 3x3x2 grid around agent to "see" what's around us
        grid = self.load_grid(world_state)

        #the directions
        north = 4 - 3
        east = 4 + 1
        south = 4 + 3
        west = 4 - 1

        ok_things = ['water', 'wooden_door']
        #check grid to see what block is there
        if grid[north] in ok_things:
            action_list.append("movenorth 1")
        if grid[east] in ok_things:
            action_list.append("moveeast 1")
        if grid[south] in ok_things:
            action_list.append("movesouth 1")
        if grid[west] in ok_things:
            action_list.append("movewest 1")

        return action_list

    def act(self, world_state, agent_host, current_r ):
        """take 1 action in response to the current world state"""

        obs_text = world_state.observations[-1].text
        obs = json.loads(obs_text) # most recent observation
        self.logger.debug(obs)
        if not u'XPos' in obs or not u'ZPos' in obs:
            self.logger.error("Incomplete observation received: %s" % obs_text)
            return 0
        current_s = "%d:%d" % (int(obs[u'XPos']), int(obs[u'ZPos']))
        self.logger.debug("State: %s (x = %.2f, z = %.2f)" % (current_s, float(obs[u'XPos']), float(obs[u'ZPos'])))

        # get possible actions
        #self.actions = get_possible_actions()
        #grid = self.load_grid(world_state)
        # print 'grid: ', grid
        # print 'size of grid: ', len(grid)
        self.actions = self.get_possible_actions(world_state, current_s)
        #print 'actions: ', self.actions

        if not self.q_table_1.has_key(current_s):
            self.q_table_1[current_s] = ([0] * len(self.actions))

        if not self.q_table_2.has_key(current_s):
            self.q_table_2[current_s] = ([0] * len(self.actions))

        # update Q values
        if self.training and self.prev_s is not None and self.prev_a is not None:
            old_q_1 = self.q_table_1[self.prev_s][self.prev_a]
            old_q_2 = self.q_table_2[self.prev_s][self.prev_a]

            #with probability 50% update q_table_1 else update q_table_2
            if random.random() < 0.5:
                print 'waffles'
                self.q_table_1[self.prev_s][self.prev_a] = \
                 old_q_1 + self.alpha * (current_r + self.gamma * self.q_table_2[current_s][self.q_table_1[current_s].index(max(self.q_table_1[current_s]))] - old_q_1)
            else:
                print 'pancakes'
                #update second q_table
                self.q_table_2[self.prev_s][self.prev_a] = \
                old_q_2 + self.alpha * (current_r + self.gamma * self.q_table_1[current_s][self.q_table_2[current_s].index(max(self.q_table_2[current_s]))] - old_q_2)

        #self.drawQ( curr_x = int(obs[u'XPos']), curr_y = int(obs[u'ZPos']) )

        # select the next action E-GREEDY
        rnd = random.random()
        if rnd < self.epsilon:
            a = random.randint(0, len(self.actions) - 1)
            self.logger.info("Random action: %s" % self.actions[a])
        else:

            # create new temporary q_table from q_table 1 and q_table  if it doesn't exist
            # if not self.q_table_3.has_key(current_s):
            #     self.q_table_3[current_s] = ([0] * len(self.actions))
            # compute the new value to use instead of max, in this case the average
            q_3 = list()
            for action in range(len(self.actions)):
                 q_3.append(\
                  (self.q_table_1[current_s][action] + self.q_table_2[current_s][action]) / 2)

            #self.logger.debug("Current values: %s" % ",".join(str(x) for x in self.q_table_1[current_s]))
            # take the maximum in the current state of the newly created table_3
            # max_value = max(self.q_table_3[current_s])
            max_value = max(q_3)
            list_of_max_actions = list()
            for x in range(0, len(self.actions)):
                if q_3[x] == max_value:
                    list_of_max_actions.append(x)

            y = random.randint(0, len(list_of_max_actions)-1)
            a = list_of_max_actions[y]

            # self.logger.info("Taking q action: %s" % self.actions[a])

        # send the selected action
        agent_host.sendCommand(self.actions[a])
        self.prev_s = current_s
        self.prev_a = a

        return current_r

    def run(self, agent_host):
        """run the agent on the world"""

        total_reward = 0
        current_r = 0
        tol = 0.01

        self.prev_s = None
        self.prev_a = None

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
        prev_z = obs[u'ZPos']
        print 'Initial position:',prev_x,',',prev_z

        if save_images:
            # save the frame, for debugging
            frame = world_state.video_frames[-1]
            image = Image.frombytes('RGB', (frame.width, frame.height), str(frame.pixels) )
            iFrame = 0
            self.rep = self.rep + 1
            image.save( 'rep_' + str(self.rep).zfill(3) + '_saved_frame_' + str(iFrame).zfill(4) + '.png' )

        # take first action
        total_reward += self.act(world_state,agent_host,current_r)


        require_move = True
        check_expected_position = False

        # main loop:
        while world_state.is_mission_running:

            # wait for the position to have changed and a reward received
            print 'Waiting for data...',
            while True:
                world_state = agent_host.peekWorldState()
                if not world_state.is_mission_running:
                    print 'mission ended.'
                    break

                if len(world_state.rewards) > 0 and not all(e.text=='{}' for e in world_state.observations):
                    obs = json.loads( world_state.observations[-1].text )
                    curr_x = obs[u'XPos']
                    curr_z = obs[u'ZPos']
                    if require_move:
                        if math.hypot( curr_x - prev_x, curr_z - prev_z ) > tol:
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
            current_r = sum(r.getValue() for r in world_state.rewards)

            if save_images:
                # save the frame, for debugging
                if world_state.is_mission_running:
                    assert len(world_state.video_frames) > 0, 'No video frames!?'
                    frame = world_state.video_frames[-1]
                    image = Image.frombytes('RGB', (frame.width, frame.height), str(frame.pixels) )
                    iFrame = iFrame + 1
                    image.save( 'rep_' + str(self.rep).zfill(3) + '_saved_frame_' + str(iFrame).zfill(4) + '_after_' + self.actions[self.prev_a] + '.png' )

            if world_state.is_mission_running:
                assert len(world_state.video_frames) > 0, 'No video frames!?'
                num_frames_after_get = len(world_state.video_frames)
                assert num_frames_after_get >= num_frames_before_get, 'Fewer frames after getWorldState!?'
                frame = world_state.video_frames[-1]
                obs = json.loads( world_state.observations[-1].text )
                curr_x = obs[u'XPos']
                curr_z = obs[u'ZPos']
                print 'New position from observation:',curr_x,',',curr_z,'after action:',self.actions[self.prev_a], #NSWE
                if check_expected_position:
                    expected_x = prev_x + [0,0,-1,1][self.prev_a]
                    expected_z = prev_z + [-1,1,0,0][self.prev_a]
                    if math.hypot( curr_x - expected_x, curr_z - expected_z ) > tol:
                        print ' - ERROR DETECTED! Expected:',expected_x,',',expected_z
                        raw_input("Press Enter to continue...")
                    else:
                        print 'as expected.'
                    curr_x_from_render = frame.xPos
                    curr_z_from_render = frame.zPos
                    print 'New position from render:',curr_x_from_render,',',curr_z_from_render,'after action:',self.actions[self.prev_a], #NSWE
                    if math.hypot( curr_x_from_render - expected_x, curr_z_from_render - expected_z ) > tol:
                        print ' - ERROR DETECTED! Expected:',expected_x,',',expected_z
                        raw_input("Press Enter to continue...")
                    else:
                        print 'as expected.'
                else:
                    print
                prev_x = curr_x
                prev_z = curr_z
                # act
                total_reward += self.act(world_state, agent_host, current_r)

        # process final reward
        self.logger.debug("Final reward: %d" % current_r)
        total_reward += current_r

        # update Q values
        if self.training and self.prev_s is not None and self.prev_a is not None:
            old_q_1 = self.q_table_1[self.prev_s][self.prev_a]
            old_q_2 = self.q_table_2[self.prev_s][self.prev_a]

            self.q_table_1[self.prev_s][self.prev_a] = old_q_1 + self.alpha * (current_r - old_q_1)
            self.q_table_2[self.prev_s][self.prev_a] = old_q_2 + self.alpha * (current_r - old_q_2)

        #self.drawQ()

        return total_reward

    def drawQ( self, curr_x=None, curr_y=None ):
        if self.canvas is None or self.root is None:
            return
        self.canvas.delete("all")
        action_inset = 0.1
        action_radius = 0.1
        curr_radius = 0.2
        action_positions = [ ( 0.5, 1-action_inset ), ( 0.5, action_inset ), ( 1-action_inset, 0.5 ), ( action_inset, 0.5 ) ]
        # (NSWE to match action order)
        min_value = -20
        max_value = 20
        for x in range(world_x):
            for y in range(world_y):
                s = "%d:%d" % (x,y)
                self.canvas.create_rectangle( (world_x-1-x)*scale, (world_y-1-y)*scale, (world_x-1-x+1)*scale, (world_y-1-y+1)*scale, outline="#fff", fill="#000")
                for action in range(4):
                    if not s in self.q_table_1:
                        continue
                    value = self.q_table_1[s][action]
                    color = 255 * ( value - min_value ) / ( max_value - min_value ) # map value to 0-255
                    color = max( min( color, 255 ), 0 ) # ensure within [0,255]
                    color_string = '#%02x%02x%02x' % (255-color, color, 0)
                    self.canvas.create_oval( (world_x - 1 - x + action_positions[action][0] - action_radius ) *scale,
                                             (world_y - 1 - y + action_positions[action][1] - action_radius ) *scale,
                                             (world_x - 1 - x + action_positions[action][0] + action_radius ) *scale,
                                             (world_y - 1 - y + action_positions[action][1] + action_radius ) *scale,
                                             outline=color_string, fill=color_string )
        if curr_x is not None and curr_y is not None:
            self.canvas.create_oval( (world_x - 1 - curr_x + 0.5 - curr_radius ) * scale,
                                     (world_y - 1 - curr_y + 0.5 - curr_radius ) * scale,
                                     (world_x - 1 - curr_x + 0.5 + curr_radius ) * scale,
                                     (world_y - 1 - curr_y + 0.5 + curr_radius ) * scale,
                                     outline="#fff", fill="#fff" )
        self.root.update()

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately

agent_host = MalmoPython.AgentHost()

# add some args
agent_host.addOptionalStringArgument('mission_file',
    'Path/to/file from which to load the mission.', '../Sample_missions/waterworld.xml')
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

if agent_host.receivedArgument("test"):
    exit(0) # can't test any further because mission_file path unknowable TODO: find a way to run this sample as an integration test

# -- set up the python-side drawing -- #
# scale = 40
# world_x = 6
# world_y = 14
# root = tk.Tk()
# root.wm_title("Q-table")
# canvas = tk.Canvas(root, width=world_x*scale, height=world_y*scale, borderwidth=0, highlightthickness=0, bg="black")
# canvas.grid()
# root.update()

if agent_host.receivedArgument("test"):
    num_maps = 1
else:
    num_maps = 30000

for imap in xrange(num_maps):

    # -- set up the agent -- #
    actionSet = ["movenorth 1", "movesouth 1", "movewest 1", "moveeast 1"]

    agent = TabQAgent(
        actions=actionSet,
        epsilon=agent_host.getFloatArgument('epsilon'),
        alpha=agent_host.getFloatArgument('alpha'),
        gamma=agent_host.getFloatArgument('gamma'),
        debug = agent_host.receivedArgument("debug")
        #canvas = canvas,
        #root = root)
        )
    # -- set up the mission -- #
    mission_file = agent_host.getStringArgument('mission_file')
    with open(mission_file, 'r') as f:
        print "Loading mission from %s" % mission_file
        mission_xml = f.read()
        my_mission = MalmoPython.MissionSpec(mission_xml, True)
    my_mission.removeAllCommandHandlers()
    my_mission.allowAllDiscreteMovementCommands()
    my_mission.requestVideo( 320, 240 )
    my_mission.setViewpoint( 1 )
    # add holes for interest
    # for z in range(2,12,2):
    #     x = random.randint(1,3)
    #     my_mission.drawBlock( x,45,z,"lava")

    my_clients = MalmoPython.ClientPool()
    my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000)) # add Minecraft machines here as available

    max_retries = 3
    agentID = 0
    expID = 'tabular_q_learning'

    num_repeats = 1
    cumulative_rewards = []
    for i in range(num_repeats):

        print "\nMap %d - Mission %d of %d:" % ( imap, i+1, num_repeats )

        my_mission_record = MalmoPython.MissionRecordSpec( "./save_%s-map%d-rep%d.tgz" % (expID, imap, i) )
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
                    time.sleep(2.5)

        print "Waiting for the mission to start",
        world_state = agent_host.getWorldState()
        while not world_state.has_mission_begun:
            sys.stdout.write(".")
            time.sleep(0.1)
            world_state = agent_host.getWorldState()
            for error in world_state.errors:
                print "Error:",error.text
        print

        # -- run the agent in the world -- #
        cumulative_reward = agent.run(agent_host)
        print 'Cumulative reward: %d' % cumulative_reward
        cumulative_rewards += [ cumulative_reward ]

        # -- clean up -- #
        time.sleep(0.5) # (let the Mod reset)

    print "Done."

    print
    print "Cumulative rewards for all %d runs:" % num_repeats
    print cumulative_rewards

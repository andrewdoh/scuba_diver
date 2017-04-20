---
layout: default
title: Proposal
---

##Summary:
The main idea for our project is to teach our agent how to fire an arrow at a target given various circumstances. The environment in whicb the agent will be operating in will change to make it more difficult for the agent to accomplish the stated goal. For example in one of our testing environment, the agent will have to shoot a moving enemy and through observing the patterns of the mobs' movements will the agent achieve a higher accuracy percentage. The input that the agents will take in will be its starting position and the targets position and the output that the agent will produce is the angle at which the arrows will hit the provided target the most. 

##AI/ML Algoritms:
We will be planning to use MDPs.

##Evaluation Plan:
The end goal of this project is that we can develop an agent that can shoot a moving target given that the target is within a reasonable distance. The metrics that are measured to determine how successful and how much reward is given to the agent is based off the distance from the arrow to the designated target. Our agent will allowed to shoot 20 arrows and the final accuracy will be recorded. Our hope is that by the end of the project, our agent will be able to achieve an 80% accuracy overall. 

As state above, the methodology in which we measure the success of our project is reliant on how accurate our agent will be. For our basic/sanity cases, we will place the agent in a basic environment where there is no added variables or obsctrutions and allow it to shoot a non-moving target. We can ,then, verify if the algorithm is working by recording the distance from the location of where the arrow landed to the target. If the distance decreases as more arrows are shot, it will prove that our agent is improving. Our dream case is that we hope the agent can achieve a 95% accuracy overall when we have both the agent and the target moving simultaneously while having multiple influencing factors like water, height, and etc.

def teleportDown(self, agent_host, teleport_x, teleport_y ,teleport_z):
            """Directly teleport to a specific position with respects to waterworld"""
            newY = teleport_y - 5
            tp_command = "tp " + str(teleport_x)+ " " + str(newY)  + " " + str(teleport_z)
            agent_host.sendCommand(tp_command)

def teleportUp(self, agent_host, teleport_x, teleport_y ,teleport_z):
            """Directly teleport to a specific position with respects to waterworld"""
            newY = teleport_y + 5
            tp_command = "tp " + str(teleport_x)+ " " + str(newY)  + " " + str(teleport_z)
            agent_host.sendCommand(tp_command)


#teleport_x, teleport_y, teleport_z is is the current x,y,z axis

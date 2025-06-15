#
# audio_power.py - Sound energy and power.
# Copyright (C) 2016  Hanson Robotics
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301  USA

import rospy
from atomic_msgs import AtomicMsgs

from hr_msgs.msg import audiodata

'''
    This implements a ROS node that subscribes to the `audio_sensors`
    topic, and passes the audio power data to the cogserver. This is
    used by OpenCog to react to loud sounds, sudden changes, and
    general background noise levels.

    An enhancement would be a a neural net that responded to clapping,
    cheering, or other common sound events, identified them, labelled
    them, and passed them on into the atomspace.
'''

class AudioPower:
	def __init__(self):
		self.atomo = AtomicMsgs()
		rospy.Subscriber("audio_sensors", audiodata, self.audio_cb)

	def audio_cb(self, data):
		#print "SuddenChange {}".format(data.SuddenChange)
		if data.SuddenChange:
			print "Heard a loud bang!"
			self.atomo.audio_bang(1.0)
		else:
			self.atomo.audio_bang(0.0)

		self.atomo.audio_energy(data.Decibel)

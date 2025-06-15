#
# atomic_msgs.py - Send data to the cogserver/atomspace.
#
# Copyright (C) 2015,2016,2017  Linas Vepstas
# Copyright (C) 2016,2017  Hanson Robotics
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3 as
# published by the Free Software Foundation and including the exceptions
# at http://opencog.org/wiki/Licenses
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to:
# Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from netcat import netcat

# The code here is a quick, cheap hack to place information into the
# cogserver atomspace. It opens a socket to the cogserver, and sends
# scheme snippets across.  These areu usually some Atomese.
#
class AtomicMsgs:

	def __init__(self):
		self.hostname = "localhost"
		self.port = 17001
		self.OCTOMAP_NAME = "faces"
		self.SPATIAL_RESOLUTION = "0.1"
		self.TIME_RESOLUTION = "10"
		self.TIME_UNITS = "100"

	# --------------------------------------------------------
	# Wholeshow control -- Start and stop openpsi
	def wholeshow_stop(self):
		netcat(self.hostname, self.port, "(disable-all-demos)")
		netcat(self.hostname, self.port, "(halt)")

	def wholeshow_start(self):
		netcat(self.hostname, self.port, "(enable-all-demos)")
		netcat(self.hostname, self.port, '(run)')

	# --------------------------------------------------------
	# Set the facetracking state in atomspace
	def update_ft_state_to_atomspace(self, enabled):
		if enabled:
			state = 'on'
		else:
			state = 'off'
		face = '(StateLink face-tracking-state face-tracking-%s)\n' % state
		netcat(self.hostname, self.port, face)

	# --------------------------------------------------------
	# Face-tracking stuff

	# Add a newly visible face to the atomspace.
	def add_face_to_atomspace(self, faceid):
		face = "(EvaluationLink (PredicateNode \"visible face\") " + \
		       "(ListLink (NumberNode \"" + str(faceid) + "\")))\n"
		netcat(self.hostname, self.port, face)
		print "New visible face in atomspace: ", faceid

	# Focus attention on specific face.
	# Build string to force attention to focus on the requested face.
	# This bypasses the normal "new face is visible" sequence, and
	# immediately shifts Eva's attention to this face.
	def add_tracked_face_to_atomspace(self, faceid):
		face = '(StateLink request-eye-contact-state (NumberNode "' + \
		       str(faceid) + '"))\n'
		netcat(self.hostname, self.port, face)
		print "Force focus of attention on face: ", faceid

	# Remove a face (make it no longer visible).
	def remove_face_from_atomspace(self, faceid):

		# AtomSpace cog-delete takes handle as an argument.
		msg = self.delete_face(faceid)
		netcat(self.hostname, self.port, msg)
		print "Removed face from atomspace: ", faceid

	# Build string to delete the face, and also to garbage-collect
	# the ListLink and NumberNode.  In the long run, explicit deletes
	# should not be needed, because the attention-allocation code
	# should do this.  However, attention-alloc does not yet work.
	def delete_face(self, faceid):

		# Delete the association between the recognized and tracked face.
		pattern = "(EvaluationLink (Predicate \"name\") " + \
			"(ListLink (ConceptNode \"" + str(faceid) + "\") " + \
			"(VariableNode \"reco-id\")))"

		# XXX FIXME -- need to also delete the ListLink above.
		del_reco = "(cog-execute! (PutLink (DeleteLink " + pattern + \
				") (GetLink " + pattern + ")))\n"
		face = del_reco + \
				"(cog-delete " + \
				"  (EvaluationLink (PredicateNode \"visible face\") " + \
				"    (ListLink (NumberNode \"" + str(faceid) + "\"))))\n" + \
				"(cog-delete " + \
				"  (ListLink (NumberNode \"" + str(faceid) + "\")))\n" + \
				"(cog-delete (NumberNode \"" + str(faceid) + "\"))\n"
		return face

	def create_face_octomap(self):
		ldcmd = '(use-modules (opencog pointmem))'
		cmd = '(cog-pointmem-create-map (ConceptNode "'+self.OCTOMAP_NAME+'") \
               (ListLink (NumberNode "'+ self.SPATIAL_RESOLUTION+'") \
                         (NumberNode "'+ self.TIME_RESOLUTION+'") \
                         (NumberNode "'+ self.TIME_UNITS+'")))'
		cmd = ldcmd + "\n" + cmd + "\n"
		print("Sending message %s " % cmd)
		netcat(self.hostname, self.port, cmd)

	# Face postions in the space-server
	def update_face_octomap(self, faceid, xx, yy, zz):
		face = '(cog-pointmem-map-atom (ConceptNode "'+self.OCTOMAP_NAME+'") \
               (NumberNode "'+ str(faceid)+'" (av 5 0 0)) \
               (ListLink (NumberNode "'+ str(xx)+'") \
                         (NumberNode "'+ str(yy)+'") \
                         (NumberNode "'+ str(zz)+'")))'
		face = face + "\n"
		print("Sending message %s " % face)
		netcat(self.hostname, self.port, face)

	# --------------------------------------------------------

	def face_recognition(self, tracker_id, name):
		'''
		Associate a face-recognition ID with a face-tracker ID.

		`tracker_id` is the ID that the 3D face-location tracker is using.
		Currently, the tracker-ID is an integer, stored as a NumberNode
		in the atomspace.

		`rec_id` is "0" for an unrecognized face and some other string
		for a recognized face. It is currently stored as a ConceptNode.
		'''
		fc = '(make-recognized-face ' + str(tracker_id) + ' "' + name + '")\n'
		netcat(self.hostname, self.port, fc)

	# --------------------------------------------------------
	# Speech-to-text stuff
	def who_said(self, stt):
		spoke = "(who-said? \"" + stt + "\")\n"
		netcat(self.hostname, self.port, spoke)

	# Pass the text that STT heard into opencog.
	# Rather than setting state, we're going to trigger a script, here.
	def perceived_text(self, text):
		netcat(self.hostname, self.port,
			'(cog-evaluate! (PutLink (DefinedPredicate "heard text")' +
			' (SentenceNode "' + text + '")))')

	# Affect in speech
	# Indicate that the robot heard freindly speech
	def affect_happy(self):
		netcat(self.hostname, self.port, "(State chat-affect chat-happy)")

	# Indicate that the robot heard negative speech
	def affect_negative(self):
		netcat(self.hostname, self.port, "(State chat-affect chat-negative)")

	# --------------------------------------------------------
	# Text-to-speech stuff
	# Let atomspace know that vocalization has started or ended.
	def vocalization_started(self):
		netcat(self.hostname, self.port, "(State chat-state chat-start)")

	def vocalization_ended(self):
		netcat(self.hostname, self.port, "(State chat-state chat-stop)")

	# --------------------------------------------------------
	# Sound localization -- send 3D xyz coordinate of sound source
	def update_sound(self, x, y, z):
		snd = "(map-sound " + str(x) + " " + str(y) + " " + str(z) + ")\n"
		netcat(self.hostname, self.port, snd)

	def audio_energy(self, decibel):
		# A StateLink is used because evaluation of psi-rules should
		# only depend on the most recent value.
		deci = '(StateLink (AnchorNode "Decibel value") ' + \
			' (NumberNode ' + str(decibel) + '))\n'
		netcat(self.hostname, self.port, deci)

	# Louds bands, explosions, hand-claps, shouts.
	def audio_bang(self, decibel):
		loud = '(StateLink (AnchorNode "Sudden sound change value")' + \
			' (NumberNode ' + str(decibel) + '))\n'
		netcat(self.hostname, self.port, loud)

	#saliency location
	#Degree of the salient point
	def saliency(self, x, y, z, deg):
		sal = '(StateLink (AnchorNode "Salient location")' + \
			'(List (NumberNode '+ str(x)+ ')' + \
			'  (NumberNode '+ str(y) + ')' + \
			'  (NumberNode '+ str(z) + ')))\n' + \
			'(StateLink (AnchorNode "Salient degree")' + \
			'  (NumberNode '+ str(deg) + '))\n'
		netcat(self.hostname, self.port, sal)

	#room luminance <=25 - dark, <=40 - normal, >40 - bright
	def room_brightness(self, bright):
		room = '(StateLink (AnchorNode "luminance")' +\
			' (NumberNode ' + str(bright) +'))\n'
		netcat(self.hostname, self.port, room)

	# --------------------------------------------------------
	# Generic
	def evaluate_scm(self, scm_string):
		netcat(self.hostname, self.port, scm_string)

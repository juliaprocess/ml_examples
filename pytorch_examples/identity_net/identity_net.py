#!/usr/bin/env python

import torch
from torch.autograd import Variable
import numpy as np
import numpy.matlib
import torch.nn.functional as F
import time 
import scipy.linalg

class identity_net(torch.nn.Module):
	def __init__(self, db, add_decoder=False, learning_rate=0.001):
		super(identity_net, self).__init__()

		self.db = db
		self.add_decoder = add_decoder
		self.learning_rate = learning_rate
		self.input_size = db['net_input_size']
		self.net_depth = db['net_depth']
		self.width_scale = db['width_scale']		#	1 is double of input size, 2 is 4 times
		self.net_width = 2*db['net_input_size']*self.width_scale
		

		self.l0 = torch.nn.Linear(self.input_size, self.net_width , bias=True)
		for l in range(self.net_depth-2):
			lr = 'self.l' + str(l+1) + ' = torch.nn.Linear(' + str(self.net_width) + ', ' + str(self.net_width) + ' , bias=True)'
			exec(lr)

		lr = 'self.l' + str(self.net_depth-1) + ' = torch.nn.Linear(' + str(self.net_width) + ', ' + str(self.input_size) + ' , bias=True)'
		exec(lr)
		exec('self.l' + str(self.net_depth-1) + '.activation = "none"')		#softmax, relu, tanh, sigmoid, none


		if add_decoder:
			lr = 'self.l' + str(self.net_depth) + ' = torch.nn.Linear(' + str(self.input_size) + ', ' + str(self.net_width) + ' , bias=True)'
			exec(lr)

			for l in range(self.net_depth-2):
				lr = 'self.l' + str(self.net_depth+1+l) + ' = torch.nn.Linear(' + str(self.net_width) + ', ' + str(self.net_width) + ' , bias=True)'
				exec(lr)
	
			lr = 'self.l' + str(2*self.net_depth-1) + ' = torch.nn.Linear(' + str(self.net_width) + ', ' + str(self.input_size) + ' , bias=True)'
			exec(lr)
			exec('self.l' + str(2*self.net_depth-1) + '.activation = "none"')		#softmax, relu, tanh, sigmoid, none





		self.output_network()
		self.initialize_network()

	def output_network(self):
		print('\tDimension Reduction Network')
		for i in self.children():
			try:
				print('\t\t%s , %s'%(i,i.activation))
			except:
				print('\t\t%s '%(i))


	def get_optimizer(self):
		return torch.optim.Adam(self.parameters(), lr=self.learning_rate)

	def mse_loss(self, x, y):
	    return torch.sum((x - y) ** 2)
		

	def initialize_network(self):
		db = self.db

		atom = np.array([[1],[-1]])
		col = np.matlib.repmat(atom, self.width_scale, 1)
		z = np.zeros(((self.input_size-1)*2*self.width_scale, 1))
		one_column = np.vstack((col, z))
		original_column = np.copy(one_column)

		eyeMatrix = torch.eye(self.net_width)

		for i in range(self.input_size-1):
			one_column = np.roll(one_column, 2*self.width_scale)
			original_column = np.hstack((original_column, one_column))

		original_column = (1.0/self.width_scale)*original_column
		original_column = torch.tensor(original_column)

		for i, param in enumerate(self.parameters()):
			#print(i)
			if len(param.data.shape) == 1:
				param.data = torch.zeros(param.data.size())
			else:
				if i == 0: 
					param.data = original_column
				elif i == self.net_depth*2-2:
					param.data = original_column.t()
				else:
					param.data = eyeMatrix

		#for i, param in enumerate(self.parameters()):
		#	print(param.data)


			#if(len(param.data.numpy().shape)) > 1:
			#	torch.nn.init.kaiming_normal_(param.data , a=0, mode='fan_in')	
			#else:
			#	pass
			#	#param.data = torch.zeros(param.data.size())

		#self.num_of_linear_layers = 0
		#for m in self.children():
		#	if type(m) == torch.nn.Linear:
		#		self.num_of_linear_layers += 1


		#	If using L21 regularizer
		#hsic_cost = HSIC_AE_objective(self, db)
		#each_L1 = np.sum(np.abs(z), axis=1)
		#L12_norm = np.sqrt(np.sum(each_L1*each_L1))
		#db['λ_0_ratio'] = np.abs(hsic_cost/L12_norm)
		#db['λ'] = float(db['λ_ratio'] * db['λ_0_ratio'])



	def gaussian_kernel(self, x, σ):			#Each row is a sample
		bs = x.shape[0]
		K = self.db['dataType'](bs, bs)
		K = Variable(K.type(self.db['dataType']), requires_grad=False)		

		for i in range(bs):
			dif = x[i,:] - x
			K[i,:] = torch.exp(-torch.sum(dif*dif, dim=1)/(2*σ*σ))

		return K

	def forward(self, y0):
		self.y0 = y0

		for m, layer in enumerate(self.children(),0):
			print(m , layer)

			cmd = 'self.y' + str(m+1) + ' = F.relu(self.l' + str(m) + '(self.y' + str(m) + '))'
			print(cmd)
			#cmd2 = var + '= F.dropout(' + var + ', training=self.training)'
			#exec(cmd)

			import pdb; pdb.set_trace()



#			if m == self.net_depth*2:
#				cmd = 'self.y_pred = self.l' + str(m) + '(y' + str(m-1) + ')'
#				exec(cmd)
#				break;
#			elif m == self.net_depth:
#				if self.add_decoder:
#					var = 'y' + str(m)
#					cmd = var + ' = self.l' + str(m) + '(y' + str(m-1) + ')'
#					exec(cmd)
#				else:
#					cmd = 'self.y_pred = self.l' + str(m) + '(y' + str(m-1) + ')'
#					exec(cmd)
#					return [self.y_pred, self.y_pred]
#
#			else:
#				cmd = 'self.y' + str(m) + ' = F.relu(self.l' + str(m) + '(y' + str(m-1) + '))'
#				#cmd2 = var + '= F.dropout(' + var + ', training=self.training)'
#				exec(cmd)
#				#exec(cmd2)

		
		exec('self.fx = y' + str(self.net_depth))
		return [self.y_pred, self.fx]


import numpy as np
import scipy as sp
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import ListedColormap

# x +:right, -:left
# y +:back, -:front
# z +:top, -:bottom

#####################################################################
def cuboid_data(pos, size=(1,1,1)):
    # code taken from
    # https://stackoverflow.com/a/35978146/4124317
    # suppose axis direction: x: to left; y: to inside; z: to upper
    # get the (left, outside, bottom) point
    o = [a - b / 2 for a, b in zip(pos, size)]
    # get the length, width, and height
    l, w, h = size
    x = [[o[0], o[0] + l, o[0] + l, o[0], o[0]],  
         [o[0], o[0] + l, o[0] + l, o[0], o[0]],  
         [o[0], o[0] + l, o[0] + l, o[0], o[0]],  
         [o[0], o[0] + l, o[0] + l, o[0], o[0]]]  
    y = [[o[1], o[1], o[1] + w, o[1] + w, o[1]],  
         [o[1], o[1], o[1] + w, o[1] + w, o[1]],  
         [o[1], o[1], o[1], o[1], o[1]],          
         [o[1] + w, o[1] + w, o[1] + w, o[1] + w, o[1] + w]]   
    z = [[o[2], o[2], o[2], o[2], o[2]],                       
         [o[2] + h, o[2] + h, o[2] + h, o[2] + h, o[2] + h],   
         [o[2], o[2], o[2] + h, o[2] + h, o[2]],               
         [o[2], o[2], o[2] + h, o[2] + h, o[2]]]               
    return np.array(x), np.array(y), np.array(z)

def plotCubeAt(alpha, pos=(0,0,0), ax=None):
    # Plotting a cube element at position pos
    if ax !=None:
        X, Y, Z = cuboid_data( pos )
        ax.plot_surface(Z, Y, X, color=[0,0,1,alpha], edgecolor='none', rstride=1, cstride=1)

def plotMatrix(ax, matrix, thr):
    # plot a Matrix 
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            for k in range(matrix.shape[2]):
                if matrix[i,j,k] >= thr:
                    # to have the 
                    plotCubeAt(matrix[i,j,k], pos=(i-0.5,j-0.5,k-0.5), ax=ax)
#####################################################################

class FeMat:
    #
    def __init__(self, nz, ny, nx):
        self.nz = nz
        self.ny = ny
        self.nx = nx
        nq = nz * ny * nx * 3
        self.m = lil_matrix((nq, nq))
    #
    def sub_ix(self, nnodes):
        q_n = np.empty(0)
        for node in nnodes:
            serpos = (node[0] * self.ny + node[1]) * self.nx + node[2]
            for dim in range(3):
                q_n = np.append(q_n,  serpos * 3 + dim)
        return np.ix_(q_n, q_n)
#
class FeVec:
    #
    def __init__(self, nz, ny, nx):
        self.nz = nz
        self.ny = ny
        self.nx = nx
        nq = nz * ny * nx * 3
        self.m = lil_matrix((nq, 1))
    #
    def sub_ix(self, nnodes):
        q_n = []
        for node in nnodes:
            serpos = (node[0] * self.ny + node[1]) * self.nx + node[2]
            for dim in range(3):
                q_n.append(int(serpos * 3 + dim))
        return q_n
    #
    def ix(self, z, y, x, d):
        return ((z * self.ny + y) * self.nx + x) * 3 + d
#
class TopolOpt3D:
    #
    @classmethod
    def neibor_nodes(cls, elem):
        nodes = np.empty(0)
        for ofst in np.ndindex(2, 2, 2):
            nodes = np.append(nodes, np.array(elem) + np.array(ofst))
        return nodes.reshape((2 ** 3, 3))
    #
    @classmethod
    def dNdX(cls, node, k, lgpt):
        if k == 0:
            return node[0] * (1.0 + node[1] * lgpt[1]) * (1.0 + node[2] * lgpt[2]) / (2 ** 3)
        elif k == 1:
            return (1.0 + node[0] * lgpt[0]) * node[1] * (1.0 + node[2] * lgpt[2]) / (2 ** 3)
        elif k == 2:
            return (1.0 + node[0] * lgpt[0]) * (1.0 + node[1] * lgpt[1]) * node[2] / (2 ** 3)
        else:
            assert False, 'invalid k={}'.format(k)
            return 0
    #
    def solve(self, (nz, ny, nx), slen, vratio):
        # Configuration
        self.nz = nz
        self.nx = nx
        self.ny = ny
        self.slen = slen
        self.vratio = vratio
        self.nu = 0.3
        self.E = 1.0
        self.Emin = 0.001
        self.pnl = 3
        max_i = 10
        # Initialization
        rho = self.vratio * np.ones((self.nz, self.ny, self.nx))
        self.K_E1 = self.calc_K_E1()
        # Iteration
        i = 0
        while i < max_i: # TODO
            u, l = self.ana_fe(rho)
            dldr = self.ana_fe_sens(rho, u)
            rho_new = self.update_oc(rho, dldr)
            #
            print('{0:5}: l:{1}'.format(i, l))
            #
            # TODO
            #
            if False:
                um = u.m.toarray()
                um = np.reshape(um, (self.nz + 1, self.ny + 1, self.nx + 1, 3))
                #plt.plot(um[self.nz / 2, self.ny / 2, :, 2])
                plt.imshow(um[self.nz / 2, :, :, 2]); plt.colorbar()
                plt.show()
            if False:
                plt.imshow(rho[self.nz / 2, :, :], vmin = 0.0, vmax = 1.0, cmap = cm.binary)
                plt.colorbar()
                plt.show()
            if False: #i == max_i - 1:
                for z in range(self.nz):
                    plt.imshow(rho[z, :, :], vmin = 0.0, vmax = 1.0, cmap = cm.binary)
                    plt.colorbar()
                    plt.show()
            if i == max_i - 1:
                fig = plt.figure()
                ax = fig.gca(projection='3d')
                ax.set_aspect('equal')
                plotMatrix(ax, rho, 0.9)
                plt.show()
            if False: #i == max_i - 1:
                #plt.imshow(rho[1, :, :], vmin = 0.0, vmax = 1.0, cmap = cm.binary)
                #plt.colorbar()
                #plt.show()

                xx, yy = np.meshgrid(np.arange(self.nx + 1), np.arange(self.ny + 1))

                # Choose colormap
                cmap = plt.cm.binary
                # Get the colormap colors
                my_cmap = cmap(np.arange(cmap.N))
                # Set alpha
                my_cmap[:,-1] = np.linspace(0.2, 0.8, cmap.N)
                # Create new colormap
                my_cmap = ListedColormap(my_cmap)

                fig = plt.figure()
                ax = fig.add_subplot(111, projection='3d')

                for z in range(self.nz):
                    zz = np.zeros_like(xx) + z
                    data = rho[z, :, :]
                    ax.plot_surface(xx, yy, zz, rstride=1, cstride=1, facecolors=my_cmap(data), shade=False)

                ax.set_xlim((0, self.nx))
                ax.set_ylim((0, self.ny))
                ax.set_zlim((0, self.nz))
                plt.show()

            #
            rho = rho_new
            i = i + 1
        #
        return rho
    #
    def ana_fe(self, rho):
        # Stiffness matrix
        K = FeMat(self.nz + 1, self.ny + 1, self.nx + 1)
        for elem in np.ndindex(self.nz, self.ny, self.nx):
            nnodes = TopolOpt3D.neibor_nodes(elem)
            K.m[K.sub_ix(nnodes)] += self.K_E1 * self.calc_E(rho[elem])
        #
        f = FeVec(self.nz + 1, self.ny + 1, self.nx + 1)
        # Forced node indices
        force_ixs = np.empty(0)
        force_ixs = np.append(force_ixs, f.ix(self.nz / 2, self.ny / 2, self.nx, 1)) # TODO: configurable
        f.m[force_ixs] = 0.01 # TODO: what unit is?
        # Fixed node indices
        fix_ixs = np.empty(0)
        for zy in np.ndindex(self.nz + 1, self.ny + 1):
            for d in range(3):
                fix_ixs = np.append(fix_ixs, f.ix(zy[0], zy[1], 0, d)) # TODO: configurable
        #
        # Replace fixing f with fixed u
        K.m[:, fix_ixs] = 0 # fixed u = 0
        K.m[fix_ixs, fix_ixs] = -1 # move fixing f to left-hand side
        #
        # Solve Ku = f
        u = FeVec(self.nz + 1, self.ny + 1, self.nx + 1)
        u.m[:] = spsolve(K.m.tocsr(), f.m).reshape((-1, 1))
        #
        # Undo replace fixing f with fixed u
        f.m[fix_ixs] = u.m[fix_ixs] # fixing f
        u.m[fix_ixs] = 0 # fixed u = 0
        #
        # Mean Compliance
        l = u.m.transpose().dot(K.m.dot(u.m))[0, 0]
        #
        return u, l
    #
    def ana_fe_sens(self, rho, u):
        dldr = np.zeros((self.nz, self.ny, self.nx))
        #
        for elem in np.ndindex(self.nz, self.ny, self.nx):
            nnodes = TopolOpt3D.neibor_nodes(elem)
            ixs = u.sub_ix(nnodes)
            ue = u.m[ixs].toarray()
            Ke = self.K_E1 * self.calc_dEdr(rho[elem])
            dldr[elem] += ue.transpose().dot(Ke.dot(ue))[0, 0]
        #
        return dldr
    #
    def update_oc(self, rho, dldr):
        # TODO: explore
        lambdaL = 0
        lambdaU = np.max([np.max(dldr), 1.0])
        mvLim = 0.125
        dump = 0.75
        eps = 1e-3
        while (lambdaU - lambdaL) / (lambdaU + lambdaL) > eps:
            lambdaM = (lambdaU + lambdaL) / 2.0
            rho_new = np.multiply(rho, (dldr / lambdaM) ** dump)
            rho_new = np.minimum(rho_new, rho + mvLim)
            rho_new = np.minimum(rho_new, 1)
            rho_new = np.maximum(rho_new, rho - mvLim)
            rho_new = np.maximum(rho_new, 0)
            if np.mean(rho_new) - self.vratio > 0:
                lambdaL = lambdaM
            else:
                lambdaU = lambdaM
        #
        return rho_new
    #
    def calc_K_E1(self):
        nodes_E1 = TopolOpt3D.neibor_nodes((0, 0, 0)) * 2.0 - 1.0
        K_E1 = np.zeros((nodes_E1.shape[0] * 3, nodes_E1.shape[0] * 3))
        #
        lgpts = (TopolOpt3D.neibor_nodes((0, 0, 0)) * 2.0 - 1.0) * (3.0 ** (-0.5))
        #
        lamda_E1 = self.nu / ((1.0 + self.nu) * (1.0 - 2.0 * self.nu))
        mu_E1 = 1.0 / (2.0 * (1.0 + self.nu))
        #
        for a in range(nodes_E1.shape[0]):
            for i in range(3):
                q_ai = a * 3 + i
                for b in range(nodes_E1.shape[0]):
                    for j in range(3):
                        q_bj = b * 3 + j
                        #
                        k = 0
                        for lgpt in lgpts:
                            k += lamda_E1 * TopolOpt3D.dNdX(nodes_E1[b], j, lgpt) * TopolOpt3D.dNdX(nodes_E1[a], i, lgpt)
                            if i == j:
                                k += mu_E1 * TopolOpt3D.dNdX(nodes_E1[b], 0, lgpt) * TopolOpt3D.dNdX(nodes_E1[a], 0, lgpt)
                                k += mu_E1 * TopolOpt3D.dNdX(nodes_E1[b], 1, lgpt) * TopolOpt3D.dNdX(nodes_E1[a], 1, lgpt)
                                k += mu_E1 * TopolOpt3D.dNdX(nodes_E1[b], 2, lgpt) * TopolOpt3D.dNdX(nodes_E1[a], 2, lgpt)
                            k += mu_E1 * TopolOpt3D.dNdX(nodes_E1[b], i, lgpt) * TopolOpt3D.dNdX(nodes_E1[a], j, lgpt)
                        K_E1[q_ai, q_bj] = k
        #
        lgW = 1.0
        detJ = (self.slen ** 3) / (2.0 ** 3)
        return K_E1 * lgW * detJ
    #
    def calc_E(self, rho_e):
        return np.interp(rho_e ** self.pnl, [0, 1], [self.Emin, self.E])
    #
    def calc_dEdr(self, rho_e):
        return self.pnl * (rho_e ** (self.pnl - 1.0)) * (self.E - self.Emin)
        
#
#####
#
if __name__ == '__main__':
    print('numpy ver: ' + np.version.full_version)
    print('scipy ver: ' + sp.version.full_version)
    print('matplotlib ver: ' + matplotlib.__version__)
    #
    t = TopolOpt3D()
    t.solve((4, 8, 16), 1, 0.5)
#

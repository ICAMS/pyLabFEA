# Module pylabfea.basic
'''Module pylabfea.basic introduces basic methods and attributes like calculation of 
equivalent stresses and strain, conversions of 
cylindrical to principal stresses and vice versa, and the classes ``Stress`` and ``Strain``
for efficient operations with these quantities.

uses NumPy

Version: 3.2 (2020-12-30)
Author: Alexander Hartmaier, ICAMS/Ruhr-University Bochum, April 2020
Email: alexander.hartmaier@rub.de
distributed under GNU General Public License (GPLv3)'''

__all__ = ['Strain', 'Stress', 'a_vec', 'b_vec', 'eps_eq', 'polar_ang', 'ptol', 
           's_cyl', 'seq_J2', 'sp_cart', 'svoigt', 'sprinc']

import numpy as np
import sys
'''try:
    import quaternion
    av_quater = True
except:
    av_quater = False'''

#===================================
#define global methods and variables
#===================================
a_vec = np.array([1., -0.5, -0.5])/np.sqrt(1.5)
'''First unit vector spanning deviatoric stress plane (real axis)'''
b_vec = np.array([0.,  0.5, -0.5])*np.sqrt(2)  
'''Second unit vector spanning deviatoric stress plane (imaginary axis)'''
ptol = 3.e-3
'''Tolerance: Plastic yielding if yield function > ptol'''
def seq_J2(sig):
    '''Calculate J2 equivalent stress from any stress tensor
    
    Parameters
    ----------
    sig : (3,), (6,) (N,3) or (N,6) array
         (3,), (N,3): Principal stress or list of principal stresses;
         (6,), (N,6): Voigt stress
         
    Returns
    -------
    seq : float or (N,) array
        J2 equivalent stresses
    '''
    N = len(sig)
    sh = np.shape(sig)
    if sh==(3,):
        N = 1 # sig is single principle stress vector
        sprinc=np.array([sig])
    elif sh==(6,):
        N = 1 # sig is single Voigt stress
        sprinc=np.array([Stress(sig).p])
    elif sh==(N,6):
        sprinc=np.zeros((N,3))
        for i in range(N):
            sprinc[i,:] = Stress(sig[i,:]).p
    elif sh==(N,3):
        sprinc=np.array(sig)
    else:
        print('*** seq_J2: N, sh', N, sh, sys._getframe().f_back.f_code.co_name)
        raise TypeError('Error: Unknown format of stress in seq_J2')
    d12 = sprinc[:,0] - sprinc[:,1]
    d23 = sprinc[:,1] - sprinc[:,2]
    d31 = sprinc[:,2] - sprinc[:,0]
    J2  = 0.5*(np.square(d12) + np.square(d23) + np.square(d31))
    seq  = np.sqrt(J2)  # J2 eqiv. stress
    if sh==(3,) or sh==(6,): 
        seq = seq[0]
    return seq

def polar_ang(sig):
    '''Transform stresses into polar angle on deviatoric plane spanned by a_vec and b_vec
    
    Parameters
    ----------
    sig : (3,), (6,) (N,3) or (N,6) array
         (3,), (N,3): Principal stresses; 
         (6,), (N,6): Voigt stress
         
    Returns
    -------
    theta : float or (N,) array
        polar angles in deviatoric plane as positive angle between sprinc and a_vec in range [-pi,+p]
    '''
    sh = np.shape(sig) 
    N = len(sig)
    if sh==(3,):
        N = 1
        sprinc = np.array([sig])
    elif sh==(6,):
        sprinc = np.array([Stress(sig).p])
    elif sh==(N,6):
        sprinc=np.zeros((N,3))
        for i in range(N):
            sprinc[i,:] = Stress(sig[i,:]).p
    elif sh==(N,3):
        sprinc=np.array(sig)
    else:
        print('*** polar_angle: N, sh', N, sh, sys._getframe().f_back.f_code.co_name)
        raise TyeError('Error: Unknown format of stress in polar_angle')
    hyd = np.sum(sprinc,axis=1)/3.  # hydrostatic component
    dev = sprinc - hyd[:,None] # deviatoric princ. stress
    vn  = np.linalg.norm(dev,axis=1)  #norms of princ. stress vectors
    ind = np.nonzero(vn<1.e-4)[0]
    vn[ind] = 1.
    dsa = np.dot(dev/vn[:,None],a_vec)
    dsb = np.dot(dev/vn[:,None],b_vec)
    theta = np.angle(dsa + 1j*dsb)
    if sh==(3,) or sh==(6,):
        theta=theta[0]
    return theta

def sprinc(sig):
    '''Convert Voigt stress tensors into principal stresses and eigenvectors.
    
    Parameters
    ----------
    sig : (6,), (N,6), (3,3), or (N,3,3) array
        Voigt stress tensor (dim=6) or Cartesian stress tensor (dim=3x3)
        
    Returns
    -------
    spa : (3,) or (N,3) array
        Principal stresses
    eva : (3,3) or (N,3,3) array
        Eigenvectors/rotation matrices of stress tensor
    '''
    N = len(sig)
    sh = np.shape(sig)
    if sh==(3,3):
        N = 1 # sig is Cartesian single stress tensor
        st=np.array([sig])
    elif sh==(N,3,3):
        st=np.array(sig) # sig is array of Cart. stress tensors
    elif sh==(6,):
        N = 1 # sig is single Voigt stress
        st = np.zeros((3,3))
        st[0,0]=sig[0]
        st[1,1]=sig[1]
        st[2,2]=sig[2]
        st[2,1]=st[1,2]=sig[3]
        st[2,0]=st[0,2]=sig[4]
        st[1,0]=st[0,1]=sig[5]
    elif sh==(N,6):
        st=np.zeros((N,3,3))
        for i in range(N):
            st[i,0,0]=sig[i,0]
            st[i,1,1]=sig[i,1]
            st[i,2,2]=sig[i,2]
            st[i,2,1]=st[i,1,2]=sig[i,3]
            st[i,2,0]=st[i,0,2]=sig[i,4]
            st[i,1,0]=st[i,0,1]=sig[i,5]
    else:
        print('*** sprinc: N, sh', N, sh, sys._getframe().f_back.f_code.co_name)
        raise TypeError('Error: Unknown format of stress in sprinc')
        
    #calculate principal stresses and eigen vectors
    spa = np.zeros((N,3))
    eva = np.zeros((N,3,3))
    for n in range(N):
        sp, ev = np.linalg.eig(st[n]) # solve eigenvalue problem 
        #arrange principal stress components according to major force axes
        iev = np.argmax(np.abs(ev),axis=1)
        j = np.zeros(3, dtype=int)
        i0 = [i for i,x in enumerate(iev) if x == 0] # positions of indices 0
        i1 = [i for i,x in enumerate(iev) if x == 1]
        i2 = [i for i,x in enumerate(iev) if x == 2]
        k0 = len(i0)
        for i in range(k0):
            j[i] = i0[i]
        for i in range(len(i1)):
            j[k0+i] = i1[i]
        k0 += len(i1)
        for i in range(len(i2)):
            j[k0+i] = i2[i]
        ev  = np.array([ev[j[0],:], ev[j[1],:], ev[j[2],:]])
        sp = np.array([sp[j[0]], sp[j[1]], sp[j[2]]])
        #ensure positive determinant
        if np.linalg.det(ev)<0:
            ev *= -1
        spa[n,:] = sp
        eva[n,:,:] = ev
    if sh==(3,3) or sh==(6,):
        spa = spa[0]
        eva = eva[0,:,:]
    return spa, eva

def sp_cart(scyl):
    '''Convert cylindrical stress into 3D Cartesian vector of deviatoric principle stresses 
    
    Parameters
    ----------
    scyl : (2,), (3,), (N,2) or (N,3) array 
         Cylindrical stress in form (seq, theta, (optional: p))
         
    Returns
    -------
    sprinc : float or (N,) array
        principle deviatoric stress
    '''
    sh = np.shape(scyl) 
    if sh==(2,) or sh==(3,):
        scyl = np.array([scyl])
    seq = scyl[:,0]
    theta = scyl[:,1]
    sprinc = (np.tensordot(np.cos(theta), a_vec, axes=0) + 
              np.tensordot(np.sin(theta), b_vec, axes=0)) \
             *np.sqrt(2./3.)*np.array([seq,seq,seq]).T
    if sh[0]==3:
        p = scyl[:,2]
        sprinc += np.array([p,p,p]).T
    if sh==(2,) or sh==(3,):
        sprinc=sprinc[0]
    return sprinc

def svoigt(scyl, evec):
    '''Convert cylindrical stress and eigenvectors into Voigt stress tensor
    
    Parameters
    ----------
    scyl : (3,) or (N,3) array 
        Cylindrical stress in form (seq, theta, p)
    evec : (3,3) or (N,3,3) array 
        Eigenvectors of stress tensor
         
    Returns
    -------
    svoigt : (6,) or (N,6) array
        Voigt stress tensor
    '''
    #sh = np.shape(scyl) 
    #if sh==(3,):
    #    scyl = np.array([scyl])
    sp = sp_cart(scyl)
    if np.linalg.det(evec)<0:
        evec *= -1  # enforce right-handed system of eigenvectors
    st = np.diag(sp)  # diag. matrix of princ. stresses
    hh = evec@st@evec.T  # rotate back into original stress frame
    svoigt = np.array([hh[0,0], hh[1,1], hh[2,2], hh[1,2], hh[0,2], hh[0,1]]) 
    #if sh==(3,):
    #    svoigt=svoigt[0]
    return svoigt

def s_cyl(sig, mat=None):
    '''convert principal stress into cylindrical stress vector 
    
    Parameters
    ----------
    sig : (3,), (6,), (N,3) or (N,6) array 
         stress to be converted, if (3,) or (N,3) principal stress is assumed
    mat : object of class ``Material``
        Material for Hill-type principal stress (optional) 
         
    Returns
    -------
    sc : (3,) or (N,3) array
        stress in cylindrical coordinates (seq, theta, p)
    '''
    sh = np.shape(sig) 
    N = len(sig)
    if sh==(3,):
        N = 1 # sig is single principle stress vector
        sp  = np.array([sig])
        sig = np.array([[sig[0], sig[1], sig[2], 0, 0,0]])
    elif sh==(N,3):
        sp  = np.array(sig)
        sig = np.append(sig,np.zeros((N,3)), axis=1)
    elif sh==(6,):
        N = 1
        sp  = np.array([Stress(sig).princ])
        sig = np.array([sig])
    elif sh==(N,6):
        sp = sprinc(sig)[0]
    else:
        print('*** s_cyl (N,sh): ',N,sh,sys._getframe().f_back.f_code.co_name)
        raise TypeError('Error in s_cyl: Format not supported')
    sc = np.zeros((N,3))
    if mat is None:
        sc[:,0] = seq_J2(sp)
    else:
        sc[:,0] = mat.calc_seq(sig)
    sc[:,1] = polar_ang(sp)
    sc[:,2] = np.sum(sp, axis=1)/3.
    if sh==(3,) or sh==(6,):
        sc=sc[0]
    return sc

def eps_eq(eps):
    '''Calculate equivalent strain 
    
    Parameters
    ----------
    eps : (3,), (6,), (N,3) or (N,6) array
         (3,) or (N,3): Principal strains;
         (6,) or (N,6): Voigt strains
         
    Returns
    -------
    eeq : float or (N,) array
        equivalent strains
    '''
    sh = np.shape(eps)
    if sh==(6,) or sh==(3,):
        eps = np.array([eps])
        N = 1
    else:
        N = len(eps)
    #ev = np.sum(eps[:,0:3],axis=1)
    #ed = eps[:,0:3] - np.array([ev,ev,ev]).T
    if sh==(6,) or sh==(N,6):
        eeq = np.sqrt(2.*(np.sum(eps[:,0:3]*eps[:,0:3],axis=1)+0.5*np.sum(eps[:,3:6]*eps[:,3:6],axis=1))/3.)
    elif sh==(3,) or sh==(N,3):
        eeq = np.sqrt(2.*np.sum(eps[:,0:3]*eps[:,0:3],axis=1)/3.)
    else:
        print('*** eps_eq (N,sh): ',N,sh,sys._getframe().f_back.f_code.co_name)
        raise ValueError('Error in eps_eq: Format not supported')

    if sh==(6,) or sh==(3,):
        eeq = eeq[0]
    return eeq
    

#=========================
#define class for stresses
#=========================
class Stress(object):
    '''Stores and converts Voigt stress tensors into different formats, 
    calculates principle stresses, equivalent stresses and transforms into cylindrical coordinates.
    
    Parameters
    ----------
    sv : list-like object, must be 1D with length 6
        Voigt-stress components
    
    Attributes
    ----------
    voigt, v : 1d-array (size 6)
        Stress tensor in Voigt notation
    tens, t : 3x3 array
        Stress tensor in matrix notation
    princ, p : 1d-array (size 3)
        Principal stresses
    hydrostatic, h : float
        Hydrostatic stress component
    '''
    def __init__(self, sv):
        self.v=self.voigt = np.array(sv)
        #calculate (3x3)-tensorial representation
        self.t=self.tens = np.zeros((3,3))
        self.tens[0,0]=sv[0]
        self.tens[1,1]=sv[1]
        self.tens[2,2]=sv[2]
        self.tens[2,1]=self.tens[1,2]=sv[3]
        self.tens[2,0]=self.tens[0,2]=sv[4]
        self.tens[1,0]=self.tens[0,1]=sv[5]
        #calcualte principal stresses and eigen vectors
        self.princ, self.evec = sprinc(self.tens)
        self.p = self.princ
        self.h = self.hydrostatic = np.sum(self.p)/3.
        self.d = self.dev = sv - np.array([self.h, self.h, self.h, 0., 0., 0.])
            
    def seq(self, mat):
        '''calculate Hill-type equivalent stress, invokes corresponding method of class ``Material``
        
        Parameters
        ----------
        mat: object of class ``Material``
            containes Hill parameters and method needed for Hill-type equivalent stress
        
        Returns
        -------
        seq : float
            equivalent stress of Hill-type
        '''
        if mat.hill_6p:
            seq = mat.calc_seq(self.v)
        else:
            seq = mat.calc_seq(self.p)
        return seq
    
    def theta(self):
        '''calculate polar angle in deviatoric plane
        
        Returns
        -------
        ang : float
            polar angle of stress in devitoric plane
        '''
        ang = polar_ang(self.p)
        return ang

    def sJ2(self):
        '''calculate J2 principal stress
        
        Returns
        -------
        sJ2 : float
            equivalent stress
        '''
        sJ2 = seq_J2(self.p)
        return sJ2
    
    def cyl(self):
        '''Calculate cylindrical stress tensor
        
        Returns
        -------
        cyl : (3,) array
            stress in cylindrical form: (J2 eqiv. stress, polar angle, hydrostatic)
        '''
        cyl = np.array([seq_J2(self.p), polar_ang(self.p), self.h])
        return cyl
    
    def lode_ang(self, X):
        '''Calculate Lode angle:  
        Transforms principal stress space into hydrostatic stress, eqiv. stress, and Lode angle; 
        definition of positive cosine for Lode angle is applied
        
        Parameters
        ----------
        X : either float or object of class ``Material``
            if float: interpreted as equivalent stress
            if ``Material``: used to invoke method of class ``Material`` to calculate equivalent stress
        
        Returns
        -------
        la : float
            Lode angle
        '''
        if type(X) is float:
            seq = X # float-type parameters are interpreted as equiv. stress
        else:
            seq = self.seq(X) # otherwise parameter is Material
        J3 = np.linalg.det(self.tens - self.h*np.diag(np.ones(3)))
        hh = 0.5*J3*(3./seq)**3
        la = np.arccos(hh)/3.
        return la

    
#=======================
#define class for strain
#=======================
class Strain(object):
    '''Stores and converts Voigt strain tensors into different formats, 
    calculates principle strain and equivalent strain.
    
    Parameters
    ----------
    sv : list-like object, must be 1D with length 6
        Voigt-strain components
        
    Attributes
    ----------
    voigt, v : 1d-array (size 6)
        Strain tensor in Voigt notation
    tens, t : 3x3 array
        Strain tensor in matrix notation
    princ, p : 1d-array (size 3)
        Principal strains
    '''
    def __init__(self, sv):
        self.v=self.voigt = np.array(sv)
        #calculate (3x3)-tensorial representation
        self.t=self.tens = np.zeros((3,3))
        self.tens[0,0]=sv[0]
        self.tens[1,1]=sv[1]
        self.tens[2,2]=sv[2]
        self.tens[2,1]=self.tens[1,2]=sv[3]
        self.tens[2,0]=self.tens[0,2]=sv[4]
        self.tens[1,0]=self.tens[0,1]=sv[5]
        #calcualte principal stresses and eigen vectors
        self.princ, self.evec = np.linalg.eig(self.tens)
        self.p=self.princ
        
    def eeq(self):
        '''Calculate equivalent strain
        
        Returns
        -------
        eeq : float
            Equivalent strain
        '''
        eeq=eps_eq(self.v)
        return eeq
        
    def inv(self):
        '''Calculate inverse of strain tensor ignoring zeros.
        
        Returns
        -------
        inv : (6,) array
        '''
        inv = np.zeros(6)
        for i in range(6):
            if np.abs(self.voigt[i])>1.e-9 : inv[i] = 1./self.voigt[i]
        return inv
 

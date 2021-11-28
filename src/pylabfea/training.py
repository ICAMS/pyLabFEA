# Module pylabfea.training
'''Module pylabfea.training introduces methods to create training data for ML flow rule
in shape of unit stresses that are evenly distributed in the stress space to 
define the load cases for which the critical stress tensor at which plastic yielding
starts needs to be determined.

uses NumPy, ScipPy, MatPlotLib, sklearn, pickle, and pyLabFEA.model

Version: 4.0 (2021-11-27)
Authors: Ronak Shoghi, Alexander Hartmaier, ICAMS/Ruhr University Bochum, Germany
Email: alexander.hartmaier@rub.de
distributed under GNU General Public License (GPLv3)'''

from pylabfea.basic import seq_J2
import numpy as np
from itertools import count
from scipy.special import gamma
from scipy.optimize import root_scalar
from sklearn.metrics import mean_absolute_error, confusion_matrix, \
     ConfusionMatrixDisplay
import matplotlib.pyplot as plt

def int_sin_m(x, m):
    '''Computes the integral of sin^m(t) dt from 0 to x recursively'''
    if m == 0:
        return x
    elif m == 1:
        return 1. - np.cos(x)
    else:
        hh = (m-1)/m * int_sin_m(x, m-2) - np.cos(x)*np.sin(x)**(m-1)/m
        return hh

def primes():
    '''Returns an infinite generator of prime numbers'''
    yield from (2, 3, 5, 7)
    composites = {}
    ps = primes()
    next(ps)
    p = next(ps)
    assert p == 3
    psq = p * p
    for i in count(9, 2):
        if i in composites:  # composite
            step = composites.pop(i)
        elif i < psq:  # prime
            yield i
            continue
        else:  # composite, = p*p
            assert i == psq
            step = 2 * p
            p = next(ps)
            psq = p * p
        i += step
        while i in composites:
            i += step
        composites[i] = step

def uniform_hypersphere(d, n, method='brentq'):
    '''Generate n usnits stresse on the d dimensional hypersphere
    representing create load cases in 3D or 6D stress space 
    
    Parameters
    ----------
    d : int
        Dimension of stress space in which to create unit stresses
    n : int
        Numberof stresses to be created
        
    Returns
    -------
    points : (n,6)-array
        Unit stresses
    '''
    
    def dim_func(y, x):
        return mult * int_sin_m(y, dim-1) - x
        
    points = np.ones((n,d))
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    points[:,0] = np.sin(t)
    points[:,1] = np.cos(t)
    for dim, prime in zip(range(2, d), primes()):
        offset = np.sqrt(prime)
        mult = gamma(0.5*(dim+1)) / (gamma(0.5*dim) * np.sqrt(np.pi))

        for i in range(n):
            res = root_scalar(dim_func, args=(i*offset % 1), method=method, 
                              bracket=[0, np.pi], xtol=1.e-8) # search root of int_sin-arg in range [0, pi]
            deg = res.root
            if not res.converged:
                print('Root finding with method "{}" not converged. Rootresults={}'\
                      .format(method, res))
            for j in range(dim):
                points[i, j] *= np.sin(deg)
            points[i, dim] *= np.cos(deg)
    return points
        
def load_cases(number_3d, number_6d, method='brentq'):
    '''Generate unit stresses in principal stress space (3d) and full stress space (6d)
    
    Parameters
    ----------
    number_3d : int
        Number of principal unit stresses to be created
    number_6d : int
        Number of full unit stresses to be created
        
    Returns
    -------
    allsig : (number_3d+number6d, 6)-array
        Unit stresses
    '''
    sig_3d = np.zeros((number_3d, 6))
    sig_3d[:,0:3] = uniform_hypersphere(3, number_3d, method=method)
    sig_6d = uniform_hypersphere(6, number_6d)
    allsig = np.concatenate((sig_3d, sig_6d))
    seq = seq_J2(allsig)
    ind = np.nonzero(seq < 1.e-3)[0]
    if len(ind) > 0:
        print('WARNING: Small stresses detected:', ind)
    allsig /= seq[:, None]
    return allsig

def training_score(yf_ref,yf_ml):
    res_yf_ref = np.sign(yf_ref)
    ind = np.nonzero(np.abs(res_yf_ref)<0.9)[0]
    res_yf_ref[ind] = 1. # change points with yf=0 to +1
    res_yf_ml  = np.sign(yf_ml)
    ind = np.nonzero(np.abs(res_yf_ml)<0.9)[0]
    res_yf_ml[ind] = 1. # change points with yf=0 to +1

    cm = confusion_matrix(res_yf_ref, res_yf_ml)
    print(cm)
    cmd = ConfusionMatrixDisplay(cm, display_labels=['Elastic','Plastic'])
    cmd.plot()
    plt.show()

    TP = 0
    FN = 0
    FP = 0
    TN = 0
    for i in range(len(res_yf_ref)):
        if (res_yf_ref[i] == 1) & (res_yf_ml[i] == 1):
            TP+=1
        if (res_yf_ref[i] == 1) & (res_yf_ml[i] == -1):
            FN+=1
        if (res_yf_ref[i] == -1) & (res_yf_ml[i] == 1):
            FP+=1
        if (res_yf_ref[i] == -1) & (res_yf_ml[i] == -1):
            TN+=1
    maee = mean_absolute_error(yf_ref, yf_ml)
    print("Mean Absolut Error is",maee)
    print('True Positives:',TP)
    print('False Negatives:',FN)
    print('False Positives:',FP)
    print('True Negatives:',TN)
    precision = (TP)/(TP+FP)
    print('Precision:',precision)
    Accuracy = (TP+TN)/(TP+FP+FN+TN)
    print('Accuracy:',Accuracy)
    Recall = (TP)/(TP+FN)
    print('Recall:',Recall)
    F1Score = 2*(Recall * precision) / (Recall + precision)
    print('F1score:',F1Score)
    return maee,precision,Accuracy,Recall,F1Score
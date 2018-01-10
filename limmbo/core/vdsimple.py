######################
### import modules ###
######################

import sys

from limmbo.utils.utils import verboseprint
from limmbo.utils.utils import regularize
from limix.mtset import MTSet as MTST

import pandas as pd
import time

######################
### core functions ###
######################

def vd_reml(datainput, cache=False, output=None, iterations=10, 
        verbose=True ):
    r"""
    Compute variance decomposition of phenotypes into genetic and noise
    covariance via standard REM: approach implemented in LIMIX

    Parameters:
        datainput : (:class:`DataInput`)
            object with ID-matched [N x P] phenotypes with [N] 
            individuals and [P] phenotypes and [N x N] relatedness 
            estimates 
        output : (string, optional)
            output directory with user-writing permissions; needed if 
            caching is True
        cache : (bool, optional)
            should results be cached
        verbose : (bool, optional) 
            should messages be printed to stdout

    Returns:
        (tuple): tuple containing:
            - Cg (numpy.array):
                [P x P] genetic variance component
            - Cn (numpy.array):
                [P x P] noise variance component 
            - process_time (double):
                cpu time of variance decomposition
    
    Examples:
        .. doctest::
            
            >>> import numpy
            >>> from numpy.random import RandomState
	    >>> from numpy.linalg import cholesky as chol 
            >>> from limmbo.core.vdsimple import vd_reml
            >>> from limmbo.io.input import InputData
            >>> random = RandomState(10)
            >>> N = 100
            >>> S = 1000
	    >>> P = 5
            >>> snps = (random.rand(N, S) < 0.2).astype(float)
            >>> kinship = numpy.dot(snps, snps.T) / float(10)
            >>> y  = random.randn(N, P)
	    >>> pheno = numpy.dot(chol(kinship), y)
	    >>> pheno_ID = [ 'PID{}'.format(x+1) for x in range(P)]
	    >>> samples = [ 'SID{}'.format(x+1) for x in range(N)]
            >>> datainput = InputData()
	    >>> datainput.addPhenotypes(phenotypes = pheno,
	    ...                         phenotype_ID = pheno_ID,
	    ...                         pheno_samples = samples)
	    >>> datainput.addRelatedness(relatedness = kinship,
	    ...                          relatedness_samples = samples)
	    >>> Cg, Cn, ptime = vd_reml(datainput, verbose=False)
            >>> print Cg
	    [[ 0.76299687  0.0195383  -0.06514475  0.0647744   0.26852758]
	     [ 0.0195383   0.3788103   0.03773139 -0.47340259  0.09924475]
	     [-0.06514475  0.03773139  1.05012803 -0.15264934 -0.0663069 ] 
	     [ 0.0647744  -0.47340259 -0.15264934  0.61147613 -0.08824788]  
	     [ 0.26852758  0.09924475 -0.0663069  -0.08824788  0.11987569]]
    """

    verboseprint(
        "Estimate covariance matrices based on standard REML",
        verbose=verbose)

    if cache is True and output is None:
        raise TypeError(('Output directory must be specified if caching',
            'is enabled'))
    if cache is False and output is not None:
        print('Warning: Caching is disabled, despite having supplied an '
              'output directory')
    if cache is True and output is not None:
        self.nrtraits, self.nrsamples = self.phenotypes.shape
        outfile = '{}/mtSetresults_nrsamples{}s_nrtraits{}s.h5'.format(
            output, self.nrsamples, self.nrtraits)
    else:
        outfile = None

    # time variance decomposition
    t0 = time.clock()
    vd = MTST(Y=datainput.phenotypes, R=datainput.relatedness)
    vd_result = vd.fitNull(
        cache=cache,
        fname=outfile,
        n_times=iterations,
        rewrite=True)
    t1 = time.clock()

    if vd_result['conv']:
        verboseprint("Variance decomposition via REML converged", 
                verbose=verbose)
        Cg = vd_result['Cg']
        Cn = vd_result['Cn']
    else:
        verboseprint(
            "Variance decomposition via REML did not converge", 
            verbose=verbose)
    processtime = t1 - t0

    # ensure that matrices are true positive semi-definite matrices
    Cg, Cg_ev_min = regularize(Cg, verbose=verbose)
    Cn, Cn_ev_min = regularize(Cn, verbose=verbose)

    return Cg, Cn, processtime

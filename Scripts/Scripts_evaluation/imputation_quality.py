import sys, os
#rootdir = os.path.dirname(os.getcwd())
sys.path.insert(0, os.getcwd())

import pandas as pd
import numpy as np

from Scripts.Scripts_evaluation import quality
import subprocess
import matplotlib.pyplot as plt


"""
Compute results with customized metrics from true vs. imputed data sets

"""
# reading input
dirin=snakemake.params['dir']
ftrue=snakemake.input['true_gts']
fimp=snakemake.input['imp_gts']
gconv=snakemake.params['path_gt2gl_script']
idt=snakemake.params['variant_id_type']
output_path=snakemake.output[0]

paths = {'beaglegt': {
    'true': os.path.join(dirin, ftrue),
    'imputed': os.path.join(dirin, fimp)},
    'beaglegl': {
        'true': os.path.join(dirin, ftrue.replace('.gt.', '.gl.')),
        'imputed': os.path.join(dirin, fimp)},
}


convertgtgl = True
if convertgtgl:
    cmd = 'bash {} {} {}'.format(gconv, paths['beaglegt']['true'], paths['beaglegl']['true'])
    subprocess.run(cmd, shell=True,)

qbeaglegt = quality.QualityGT(*paths['beaglegt'].values(), 0, idx=idt)
qbeaglegl = quality.QualityGL(paths['beaglegl']['true'], paths['beaglegl']['imputed'], 0, idx=idt)


try:
    entro = qbeaglegl.cross_entropy
except KeyError:
    entro = None


tabbeaglegl = pd.concat([qbeaglegt.concordance(),
                         qbeaglegt.trueobj.af_info,
                         qbeaglegt.pearsoncorrelation(),
                         qbeaglegt.precision,
                         qbeaglegt.accuracy,
                         qbeaglegt.recall,
                         qbeaglegt.f1_score,
                         entro], axis=1)
dosbeaglegl = qbeaglegt.alleledosage()


tabbeaglegl.head()


plt.rcParams["figure.figsize"] = [5*4, 4*2]
fig, axes = plt.subplots(2, 4)

tabbeaglegl.plot.scatter('af_info', 'precision_score', ax=axes[0, 0], s=0.7)
axes[0, 0].set_ylim(0.0, 1.0)
tabbeaglegl.plot.scatter('af_info', 'accuracy_score', ax=axes[0, 1], s=0.7)
axes[0, 1].set_ylim(0.0, 1.0)
tabbeaglegl.plot.scatter('af_info', 'concordance', ax=axes[0, 2], s=0.7)
axes[0, 2].set_ylim(0.0, 1.0)
tabbeaglegl.plot.scatter('af_info', 'f1_score', ax=axes[0, 3], s=0.7)
axes[0, 3].set_ylim(0.0, 1.0)
tabbeaglegl.plot.scatter('af_info', 'r_squared', ax=axes[1, 0], s=0.7)
axes[1, 0].set_ylim(-0.2, 1.0)
if entro is not None:
    tabbeaglegl.plot.scatter('af_info', 'cross_entropy', ax=axes[1, 1], s=0.7)
    axes[1, 1].set_ylim(-0.5, 5.0)
axes[1, 2].scatter(dosbeaglegl[0], dosbeaglegl[1], s=0.7)
axes[1, 2].set_xlabel('true allele dosage')
axes[1, 2].set_ylabel('imputed allele dosage')
axes[1, 2].set_ylim(0.0, 2.0)

for ax in axes.flatten()[:-2]:
    # cast color to white 'w' if dark background
    ax.set_xlabel('true alternate allele frequency', color='k')
    ax.set_ylabel(ax.get_ylabel().replace('_', ' '), color='k')
plt.suptitle('Evaluation of imputation performance')
plt.savefig(output_path)

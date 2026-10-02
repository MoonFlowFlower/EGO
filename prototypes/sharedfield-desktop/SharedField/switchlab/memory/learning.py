"""Small online availability predictor. Feedback is explicit, not user approval.

Engineered features/SGD/prior/objective; weights learn from independently keyed
contact outcomes. This does not learn ultimate values or certify social insight.
"""
import math

def initial():return {'weights':[0.,0.,0.,0.],'updates':0,'examples':0,'loss_sum':0.,'counts':{'0':[1.,1.],'1':[1.,1.]},'default_predictor':'category_beta_counts'}
def features(category,late_seconds,has_busy_report=False):
    return [1.,1. if category=='checkin' else 0.,min(4.,max(0.,late_seconds)/1800.),float(has_busy_report)]
def predict(model,x):
    z=max(-20.,min(20.,sum(w*a for w,a in zip(model['weights'],x))));return 1/(1+math.exp(-z))
def update(model,x,y):
    p=predict(model,x);loss=-(y*math.log(max(1e-9,p))+(1-y)*math.log(max(1e-9,1-p)))
    for i in range(4):model['weights'][i]=max(-6.,min(6.,model['weights'][i]+.24*(y-p)*x[i]))
    model['updates']+=1;return loss


def forecast(model,x):
    """Default after synthetic comparison: the stronger, simpler keyed estimator."""
    a,b=model['counts'][str(int(x[1]))];return a/(a+b)

def observe(model,x,y):
    """One new actual outcome. Replay must call update(), not this method."""
    model['counts'][str(int(x[1]))][0 if y else 1]+=1
    return update(model,x,y)

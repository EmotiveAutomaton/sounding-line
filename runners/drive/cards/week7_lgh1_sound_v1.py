"""Six within-recording measurements for a marked laugh; no file or identity output."""
import numpy as np


def _samples(values):
    x=np.asarray(values,dtype=float)
    if x.ndim!=1 or x.size==0 or not np.isfinite(x).all():
        raise ValueError('One finite nonempty microphone channel required')
    return x


def _pitch_and_fraction(x,rate):
    size,step=round(.04*rate),round(.01*rate)
    if len(x)<size:return np.empty(0),None
    frames=np.lib.stride_tricks.sliding_window_view(x,size)[::step]
    frame_rms=np.sqrt(np.mean(frames*frames,axis=1))
    floor=max(1e-12,.01*frame_rms.max())
    lo,hi=int(rate/600),int(np.ceil(rate/60))
    pitch=[]
    active=frame_rms>=floor
    for frame in frames[active]:
        y=frame-frame.mean()
        # Positive-lag correlation from an FFT, with per-lag energy normalization.
        fft=np.fft.rfft(y,n=2*size)
        corr=np.fft.irfft(fft*fft.conj(),n=2*size)[:hi+2]
        energy=np.r_[0.,np.cumsum(y*y)]
        lags=np.arange(len(corr))
        denom=np.sqrt(np.maximum(0.,energy[size-lags]*(energy[-1]-energy[lags])))
        corr=np.divide(corr,denom,out=np.zeros_like(corr),where=denom>0)
        top=np.where((corr[1:-1]>=corr[:-2]) & (corr[1:-1]>corr[2:]))[0]+1
        top=top[(top>=lo)&(top<=hi)&(corr[top]>=.65)]
        if not top.size:continue
        k=top[corr[top]>=.95*np.max(corr[top])][0]
        a,b,c=corr[k-1:k+2]
        delta=np.clip(.5*(a-c)/(a-2*b+c),-.5,.5) if a-2*b+c else 0.
        pitch.append(rate/(k+delta))
    active_count=int(np.count_nonzero(active))
    return np.asarray(pitch),len(pitch)/active_count if active_count else None


def _bursts(x,rate):
    step=round(.01*rate)
    levels=np.asarray([np.sqrt(np.mean(x[k:k+step]**2)) for k in range(0,len(x),step)])
    active=np.flatnonzero((levels>=.1*levels.max())&(levels>1e-12))
    if not len(active):return 0
    groups=np.split(active,np.flatnonzero(np.diff(active)>4)+1)
    return sum(int((g[-1]-g[0]+1)>=3) for g in groups)


def measures(laugh,speech,sample_rate):
    """Ephemeral per-laugh features used inside the group analysis."""
    if not isinstance(sample_rate,(int,np.integer)) or not 8000<=sample_rate<=96000:
        raise ValueError('Unsupported sampling rate')
    x,y=_samples(laugh),_samples(speech)
    pitch,fraction=_pitch_and_fraction(x,sample_rate)
    ref,_=_pitch_and_fraction(y,sample_rate)
    rms=np.sqrt(np.mean(x*x));baseline=np.sqrt(np.mean(y*y))
    semitones=12*np.log2(pitch) if len(pitch) else np.empty(0)
    rel=None if not len(ref) or not len(pitch) else float(12*np.log2(np.median(pitch)/np.median(ref)))
    return dict(duration_seconds=len(x)/sample_rate,bursts=_bursts(x,sample_rate),voiced_fraction=fraction,
                relative_pitch_semitones=rel,pitch_iqr_semitones=float(np.ptp(np.quantile(semitones,[.25,.75]))) if len(pitch) else None,
                relative_level_db=float(20*np.log10(rms/baseline)) if min(rms,baseline)>0 else None)

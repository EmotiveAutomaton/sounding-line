import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import pytest
from runners.drive.cards.week7_meeting_figures import save_figure
from runners.drive.cards.week7_icsi_recordings import LIMIT


@pytest.mark.parametrize('card',['LGH1','LGH2'])
def test_export_carries_icsi_scope(tmp_path,card):
    fig,ax=plt.subplots()
    try:
        ax.plot([0,1],[0,1])
        p=tmp_path/'made.png'
        save_figure(fig,p,card=card,corpus='ICSI',caption='Constructed group summary.')
        text=' '.join(fig.texts[-1].get_text().split())
        assert LIMIT in text and 'annotated utterance length' in text and p.stat().st_size>0
    finally:
        plt.close(fig)

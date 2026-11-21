import numpy as np
import pytest
from tests.test_week6_person_more_v1 import frame
from runners.drive.cards import week6_br_v1 as br


@pytest.mark.parametrize('member',['0056','0057','0060','0072','0076'])
def test_source_alignment_and_independent_grades(member):
    f=frame(member,8)
    for original in ([False,True] if member in ('0057','0060') else [False]):
        data=(br.base if original else br.sources).project(f,member)
        retained=br.retained(f,member,original)
        assert np.array_equal(retained.id.to_numpy(),np.unique(f.id)[data['ids']])
        for name,(event,y) in data['slopes'].items():
            column=br.grade_column(member,name)
            if column is None:
                assert member=='0072' or (member=='0060' and name.startswith('argument_'))
                continue
            grade=np.where(np.isfinite(event),retained[column]-1,np.nan)
            np.testing.assert_equal(event,np.where(np.isfinite(grade),grade>0,np.nan))
            halves=br.graded_halves(data,grade,y,data['splits']['time'],True)
            for part in halves:
                assert np.all(part['sxx'][np.isfinite(part['b'])]>0)


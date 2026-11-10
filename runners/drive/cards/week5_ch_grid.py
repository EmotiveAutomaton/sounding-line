"""Finite commissioned CH primary, branch and texture definitions.

This is a dependency specification, not launch authority. Owner review and native
fixtures precede readiness; complete measured inputs precede effect calculation.
All figures charge CH's 2,500,000 CPU-second family ceiling.
"""
CEILINGS={'CH2':60000,'CH3':40000,'CH4':80000,'CH5':40000,'CH6':30000}


def grid():
    rows=[]
    def add(card,suffix='',texture=False,branch=None,rescore=False,**config):
        row=dict(id=card+suffix,card=card,kind='texture' if texture else 'branch' if branch else 'primary',
                 requires=['CH1-complete-collection'] if card in ('CH2','CH3','CH5') else ['CH0-complete-history'],
                 module='runners.drive.cards.week5_ch_models' if card in ('CH2','CH3','CH5') else 'runners.drive.cards.week5_ch_histories',
                 config=dict(card=card,draws=200 if texture else 2000,**config),cpu_ceiling=200000 if rescore else min(3600,CEILINGS[card]) if texture else CEILINGS[card],
                 family_cpu_ceiling=2500000,projected_peak_ram_GiB=4.,generation=0 if not branch else 1)
        if branch:row['branch_condition']=dict(parent=card,outcome=branch)
        if rescore:row.update(requires=['CH1-complete-collection',f'CH1-rescore-{config["nodes"]}'],rescore_positions=25000,shared_rescore_ceiling=200000);row['config'].pop('nodes')
        rows.append(row)
    for card in CEILINGS:add(card)
    add('CH2','.m',branch='supports',critical=True)
    add('CH2','.s',branch='against',measure='entropy')
    for card in ('CH2','CH3','CH5'):
        for tc in ('bullet','blitz','rapid','classical'):
            if card in ('CH2','CH3') and tc=='blitz':continue
            add(card,'.tc-'+tc,texture=True,time_control=tc)
    for measure in ('k100','entropy','entropy_fixed100'):add('CH2','.'+measure,texture=True,measure=measure)
    for year in (2017,2026):add('CH2','.year-'+str(year),texture=True,year=year)
    for variant in ('stakes_only','complexity_only','neither'):add('CH2','.'+variant,texture=True,control_variant=variant)
    for nodes in (300000,3000000):add('CH2','.nodes-'+str(nodes),texture=True,rescore=True,nodes=nodes)
    for width in (200,800):add('CH3','.band-'+str(width),texture=True,band_width=width)
    add('CH4','.move20',texture=True,start_move=20)
    add('CH4','.rapid',texture=True,time_control='rapid')
    add('CH4','.days',texture=True,concentration_by='days')
    for threshold in (.2,.4):add('CH4','.overshoot-'+str(int(threshold*100)),texture=True,overshoot_threshold=threshold)
    for cap in (300,1000):add('CH5','.cap-'+str(cap),texture=True,loss_cap=cap)
    add('CH5','.stakes200',texture=True,max_stakes=200)
    for gap in (15,60):add('CH6','.gap-'+str(gap),texture=True,gap_minutes=gap)
    for tc in ('blitz','rapid'):add('CH6','.'+tc,texture=True,time_control=tc)
    add('CH6','.streak',texture=True,streak=True)
    for year in (2017,2026):add('CH6','.year-'+str(year),texture=True,year=year)
    return dict(cells=rows,texture_stop_after_consecutive_inside_band=7,primary_family_null_stop=6,
                uncertainty_precision_followup=2000,max_generation=2,constructed_fixture_is_science=False)

"""Read-only checks of frozen runs; writes only a separate review directory."""
from bisect import bisect_right
import csv
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path

import constructed_coupling as c


def read_csv(path):
    with path.open() as f:return list(csv.DictReader(f))


def load_run(root):
    prediction=json.loads((root/'prediction.json').read_text())
    claimed=prediction.pop('prediction_sha256')
    c.require(c.digest(prediction)==claimed,'Prediction digest changed')
    c.require(prediction['implementation_sha256']==c.IMPLEMENTATION_SHA256,'Execution used a different implementation')
    for name,expected in prediction['file_sha256'].items():
        c.require(hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,'Changed run file: '+str(root/name))
    prediction['prediction_sha256']=claimed
    return prediction


def event_stream(path,field=None,upper=None):
    with gzip.open(path,'rt') as f:
        for line in f:
            row=json.loads(line)
            if field is not None and row.get('field')!=field:continue
            if upper is not None and row['cut']>=upper:continue
            yield row


def main():
    c.check_sources()
    contract=json.loads((c.HERE/'contract.json').read_text())
    result_root=c.HERE/'results'
    cases=contract['cases']
    runs={case:load_run(result_root/case) for case in cases}
    base=runs['baseline'];added=runs['add_346_to_parent'];disabled=runs['same_addition_feedback_disabled']
    c.require(base['base_prefix_sha256']==added['base_prefix_sha256']==disabled['base_prefix_sha256'],
              'Intervention rewrote committed base events')
    c.require(base['base_trajectory_sha256']==disabled['base_trajectory_sha256'],
              'Disabled feedback did not preserve the base trajectory')
    c.require(base['base_trajectory_sha256']!=added['base_trajectory_sha256'],
              'Activated feedback made no causal difference')
    c.require(base['base_trajectory_sha256']!=runs['one_fewer_346_constituent']['base_trajectory_sha256'],
              'Inventory failed to enter the evolution')
    summary=[];times={};windows={};rd_rows={}
    for case,prediction in runs.items():
        root=result_root/case
        clos=read_csv(root/'closures.csv')
        times[case]=[int(row['cut']) for row in clos if row['field']=='P']
        windows[case]=read_csv(root/'windowed_relations.csv')
        rd_rows[case]=read_csv(root/'directional_rd_rcd.csv')
        disjoint=[row for row in windows[case] if row['kind']=='disjoint']
        total=prediction['final_counts']
        for field in ('new_parent_closures','reference_bips','parent_atomic_traversals','parent_window_load'):
            c.require(sum(int(row[field]) for row in disjoint)==total[field], 'Window projection lost events')
        checks=json.loads((root/'checks.json').read_text())
        c.require(checks['counter_conservation'],'Tick/click conservation failed')
        summary.append({'case':case,**total,'parent_return_cuts':times[case],
                        'tick_emissions_all_channels':checks['actual_tick_count'],
                        'returned_clicks_all_channels':checks['actual_click_count'],
                        'pending_currents':checks['pending_current_count'],
                        'native_directional_comparison':checks['native_P_R_comparisons']})
    differences=[]
    for case in cases[1:]:
        for index,(base_cut,other_cut) in enumerate(zip(times['baseline'],times[case]),1):
            differences.append({'case':case,'parent_reclosure':index,'baseline_cut':base_cut,
                                'comparison_cut':other_cut,'difference_in_declared_cuts':other_cut-base_cut})
    first_difference=None
    original=event_stream(result_root/'baseline/atomic_and_hinge_events.jsonl.gz','P')
    changed=event_stream(result_root/'add_346_to_parent/atomic_and_hinge_events.jsonl.gz','P')
    for a,b in zip(original,changed):
        if a!=b:
            first_difference={'baseline':a,'added_feedback':b};break
    c.require(first_difference is not None and min(first_difference[k]['cut'] for k in first_difference)
              >contract['intervention_cut'],'Causal effect preceded intervention')
    load=base['final_counts']['parent_window_load']
    c.require(load>0,'Capacity illustration requires an actual positive window load')
    capacity={'status':'unselected algebraic alternatives, not inferred nuclear capacities',
              'window':[base['formation_cut'],contract['horizon_cut']],
              'computed_nonnegative_load':load,'source':'sections/06_field.tex: eq:closure-residual; eq:shedding-excess',
              'alternatives':[{'C':str(Fraction(load,2)),'residual':str(Fraction(load,2)),
                               'surplus':str(Fraction(load,2))},
                              {'C':str(load),'residual':'0','surplus':'0'},
                              {'C':str(load+1),'residual':'-1','surplus':'0'}],
              'consequence':'The same counted trajectory does not identify a residual without capacity. Positive surplus alone also does not establish parent loss or a daughter.'}
    review=c.HERE/'review';review.mkdir(exist_ok=True)
    c.write_json(review/'summary.json',{'cases':summary,'matched_controls_pass':True,
                                       'first_parent_action_difference':first_difference,
                                       'retention_identified':False})
    c.write_csv(review/'closure_delays.csv',differences)
    c.write_json(review/'capacity_obstruction.json',capacity)
    c.write_json(review/'validation_summary.json',{
        'normal_tests':18,'optimized_tests':18,'source_files_verified':len(c.check_sources()['sha256']),
        'normal_test_log':'../checks_test_normal.log','optimized_test_log':'../checks_test_optimized.log',
        'full_runs_verified':cases,'committed_prefix_preserved':True,'disabled_feedback_restores_base':True,
        'changed_inventory_changes_trajectory':True,'window_counter_conservation':True,
        'physical_decay_prediction':False,'full_upstream_repository_suite':'not run; detached application only',
        'manuscript_build':'not applicable; no manuscript changed',
        'hosted_ci':'not changed; no remote write'})
    # A compact numerical figure is useful for comparing effects within the
    # declared model. The axis explicitly identifies cuts, never SI seconds.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4.2),layout='constrained')
    colors={'add_346_to_parent':'#b44d19','same_addition_feedback_disabled':'#606d80',
            'one_fewer_346_constituent':'#087e8b'}
    labels={'add_346_to_parent':'Added 3:4:6 feedback','same_addition_feedback_disabled':'Feedback disabled',
            'one_fewer_346_constituent':'One fewer 3:4:6 constituent'}
    for case in cases[1:]:
        selected=[x for x in differences if x['case']==case]
        axes[0].plot([x['parent_reclosure'] for x in selected],
                     [x['difference_in_declared_cuts']/1_000_000 for x in selected],
                     marker='o',color=colors[case],label=labels[case])
    axes[0].set(xlabel='Completed parent reclosure',ylabel='Delay versus baseline (million model cuts)',
                title='Coupling changes the return trajectory')
    axes[0].axhline(0,color='#aaaaaa',linewidth=.7);axes[0].legend(fontsize=8)
    quarter=[x for x in windows['baseline'] if x['kind']=='disjoint']
    axes[1].plot(range(1,len(quarter)+1),[float(Fraction(x['closures_per_reference_bip'])) for x in quarter],
                 marker='o',color='#17548b')
    for i,x in enumerate(quarter,1):
        axes[1].annotate(x['closures_per_reference_bip'],(i,float(Fraction(x['closures_per_reference_bip']))),
                         xytext=(0,7),textcoords='offset points',ha='center',fontsize=9)
    axes[1].set(xlabel='Frozen disjoint observation window',ylabel='Parent closures / reference bips',
                title='The observed ratio depends on the window')
    axes[1].set_xticks(range(1,len(quarter)+1));axes[1].margins(y=.25)
    for ax in axes:ax.grid(alpha=.2)
    fig.suptitle('Finite constructed-field experiment — no isotope decay or SI inference',fontsize=11)
    fig.savefig(review/'coupling_and_windows.png',dpi=170)
    fig.savefig(review/'coupling_and_windows.pdf')
    plt.close(fig)
    print(json.dumps({'cases':[{'case':x['case'],'closures':x['new_parent_closures'],
                              'reference_bips':x['reference_bips'],'ratio':x['closures_per_reference_bip'],
                              'closure_cuts':x['parent_return_cuts']} for x in summary],
                      'first_difference':first_difference,'capacity_load':load},indent=2))


if __name__=='__main__':main()

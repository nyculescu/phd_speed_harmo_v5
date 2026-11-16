import json,sys
d=json.load(open(sys.argv[1]))
key=sys.argv[2]
for e in d:
    if e['key']!=key: continue
    a=e['analysis']; v=e['verify']
    vd={x['id']:x for x in v['verdicts']}
    for f in a['findings']:
        print('##',f['id'],':',f.get('statement'))
        print('  NUM:',f.get('numbers'))
        x=vd.get(f['id'])
        if x: print('  VERDICT:',x.get('verdict'),'|',x.get('recomputed'),'|',x.get('note'))
    print('## ANSWER_VERDICT:',v['answer_verdict'])
    for i,m in enumerate(v['missed'],1): print('## vm%d:'%i,m)

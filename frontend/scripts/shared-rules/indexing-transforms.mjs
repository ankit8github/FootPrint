// Trusted build-only exact replacements. No rules, inputs or classifications change.
export const replacements = [
  [
    "      for (const order of [...new Set(support.flatMap(o => o.order_keys))].sort()) {\n        const sameOrder = support.filter(o => o.order_keys.includes(order));",
    `      const aliasMembers = new Map<string, EvidenceObservation[]>();
      for (const observation of support) {
        for (const alias of new Set(observation.order_keys)) {
          const members = aliasMembers.get(alias) ?? [];
          members.push(observation); aliasMembers.set(alias, members);
        }
      }
      for (const order of [...aliasMembers.keys()].sort()) {
        const sameOrder = aliasMembers.get(order)!;`,
  ],
  [
    '  const assessments: Assessment[] = [];',
    `  const assessments: Assessment[] = [];
  const sourceAdapters = new Map<string, Set<string>>();
  for (const source of graph.sources) {
    const adapters = sourceAdapters.get(source.source_id) ?? new Set<string>();
    adapters.add(source.adapter); sourceAdapters.set(source.source_id, adapters);
  }
  const primaryMembers = new Map<string, Set<string>>();
  for (const evidence of graph.relationship_evidence) {
    if (evidence.role !== 'primary') continue;
    const members = primaryMembers.get(evidence.relationship_id) ?? new Set<string>();
    members.add(evidence.observation_id); primaryMembers.set(evidence.relationship_id, members);
  }`,
  ],
  [
    "        graph.sources.some(s => s.source_id === o.source_id && s.adapter === o.adapter) &&\n        graph.relationship_evidence.some(e => e.relationship_id === relationship.id && e.observation_id === o.id && e.role === 'primary'));",
    "        sourceAdapters.get(o.source_id)?.has(o.adapter) &&\n        primaryMembers.get(relationship.id)?.has(o.id));",
  ],
  [
    "      const sameOrderConflict = evidence.some(paid => has(paid, 'PAID_RECEIPT_CLAIM') && evidence.some(cancelled =>\n        has(cancelled, 'CANCELLED_BEFORE_PAYMENT_CLAIM') && paid.order_keys.some(key => /^order\\d{4,5}$/.test(key) && cancelled.order_keys.includes(key))));",
    String.raw`      const cancelledAliases = new Set(evidence.filter(o => has(o, 'CANCELLED_BEFORE_PAYMENT_CLAIM')).flatMap(o => o.order_keys));
      const sameOrderConflict = evidence.some(paid => has(paid, 'PAID_RECEIPT_CLAIM') &&
        paid.order_keys.some(key => /^order\d{4,5}$/.test(key) && cancelledAliases.has(key)));`,
  ],
];

export function indexed(source) {
  for (const [before, after] of replacements) {
    if (source.split(before).length !== 2) throw Error('INDEX_TRANSFORM_PIN');
    source = source.replace(before, after);
  }
  return source;
}

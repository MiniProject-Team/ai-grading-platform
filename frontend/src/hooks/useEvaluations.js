import { useCallback, useEffect, useState } from 'react';
import { getEvaluations } from '../services/evaluationApi';

export function useEvaluations(filters) {
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: 20 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await getEvaluations(filters));
    } catch (requestError) {
      setError(requestError);
    } finally {
      setLoading(false);
    }
  }, [filters?.page, filters?.pageSize, filters?.studentId, filters?.examId, filters?.status]);

  useEffect(() => { load(); }, [load]);
  return { ...data, loading, error, reload: load };
}

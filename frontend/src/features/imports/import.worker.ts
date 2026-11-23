import { ParseIssue, parseSelectedFiles } from './parsers';

// This worker has no fetch, XHR, sockets, DOM or persistent storage calls.
self.onmessage = async (event: MessageEvent<File[]>) => {
  try { self.postMessage({ batch: await parseSelectedFiles(event.data) }); }
  catch (error) {
    self.postMessage({ code: error instanceof ParseIssue ? error.code : 'PARSER_FAILED' });
  }
};

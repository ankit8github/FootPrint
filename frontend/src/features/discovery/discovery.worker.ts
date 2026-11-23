import { ParseIssue } from '../imports/parsers';
import { discoverSelectedFiles } from './discovery';

// Selected bytes and transient correlation maps stay in this worker. No I/O APIs.
self.onmessage = async (event: MessageEvent<File[]>) => {
  try { self.postMessage({ graph: await discoverSelectedFiles(event.data) }); }
  catch (error) {
    self.postMessage({ code: error instanceof ParseIssue ? error.code : 'PARSER_FAILED' });
  }
};

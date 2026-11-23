import { ParseIssue } from '../imports/parsers';
import { assessSelectedFiles } from './assessments';

// No network, storage, console, DOM or external service APIs.
self.onmessage = async (event: MessageEvent<File[]>) => {
  try { self.postMessage({ result: await assessSelectedFiles(event.data) }); }
  catch (error) { self.postMessage({ code: error instanceof ParseIssue ? error.code : 'PARSER_FAILED' }); }
};

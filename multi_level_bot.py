from langchain.prompts import PromptTemplate
import doc_core as dc

def create_answer_chain(config, prompt):
    if 'collection_name' in config.keys():
      return dc.prepareAnswerChain(config['db_path'], config['collection_name'], dc.embeddings, dc.llm, prompt, config['retriever'])
    else:
      return dc.prepareSimpleAnswerChain(dc.llm, prompt)

def create_talk_bot(config):
  if 'categories' in config.keys():
    return GatewayBot(config)
  else:
    return TalkBot(config)

class TalkBot:
  def __init__(self, config):
    self.config = config
    self.name = config['name']
    self.display_name = config['display_name']
    self.description = config['description']
    self.prompt_template = config['prompt']
    prompt = PromptTemplate.from_template(self.prompt_template)
    self.answer_chain, retriever = create_answer_chain(config, prompt)

  def ask(self, question):
    return self.answer_chain.invoke(question)


class GatewayBot:
  def __init__(self, config):
    self.config = config
    self.name = config['name']
    self.display_name = config['display_name']
    self.description = config['description']
    self.prompt_template = config['prompt']
    prompt = PromptTemplate.from_template(self.prompt_template)
    self.answer_chain, retriever = create_answer_chain(config, prompt)    

    self.talk_bots = []

    for category_name, category_config in config['categories'].items():
      self.talk_bots.append(create_talk_bot(category_config))
    

  def list_talkbots(self):
    result = []
    for i, tb in enumerate(self.talk_bots):
      result.append(f"{i}. {tb.description}")
    return "\n".join(result)
  
  def ask(self, question):
    answer = self.answer_chain.invoke({"question": question, "context": self.list_talkbots()})
    if len(answer) > 2:
      return answer
    else:
      category_num = int(answer)
      print("SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSelected category_num: " + str(category_num))
      return self.talk_bots[category_num].ask(question)


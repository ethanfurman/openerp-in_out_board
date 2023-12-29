{
    'name': 'In/Out Board',
    'version': '0.1',
    'category': 'Operations/Tools',
    'description': """\
            Track in/out status from external time clock punches.
            """,
    'author': 'Ethan Furman',
    'maintainer': 'Ethan Furman',
    'website': '',
    'depends': [
            "base",
            "hr",
            ],
    'data': [
            'security/ir.model.access.csv',
            'views/in_out_board.xaml',
	    'data/ir_cron.xaml',
            ],
    'css':[
        ],
    'js': [
            ],
    'test': [],
    'application': True,
    'installable': True,
    'active': False,
}

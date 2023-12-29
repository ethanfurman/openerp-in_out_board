import logging

from antipathy import Path
from base64 import b64encode
from datetime import datetime

from odoo import api, models, fields

_logger = logging.getLogger(__name__)

MESSAGE_FILES = Path('/home/openerp/sandbox/openerp/var/in_out_board/')
ARCHIVE = MESSAGE_FILES / 'archive'
ERRORS = MESSAGE_FILES / 'errors'

for loc in (MESSAGE_FILES, ARCHIVE, ERRORS):
    if not loc.exists():
        loc.makedirs()

class InOutPunch(models.Model):
    _name = 'in_out_board.punch'
    _description = "External time-clock punch"

    timestamp = fields.Datetime('Timestamp')
    employee_no = fields.Integer('Employee #')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    image = fields.Image('Image', max_width=1024, max_height=1024)
    state = fields.Selection([('in','In'), ('out','Out')], 'State')

    @api.model
    def _process_punch_files(self):
        _logger.warning('io_out_board.punch._process_punch_files')
        hr_employee = self.env['hr.employee']
        _logger.warning('possible files: %r', MESSAGE_FILES.glob())
        for message in MESSAGE_FILES.glob():
            if message in (ARCHIVE, ERRORS):
                continue
            dest = ARCHIVE
            try:
                emp_num, state = message.base.split('-')
                timestamp = datetime.fromtimestamp(message.stat().st_mtime)
                with open(message, 'rb') as fh:
                    data = b64encode(fh.read())
                emp_id = hr_employee.search([('identification_id','=',emp_num)])[0].id
                self.create({
                        'timestamp': timestamp,
                        'employee_no': emp_num,
                        'image': data,
                        'state': state,
                        'employee_id': emp_id,
                        })
            except Exception:
                _logger.exception('unable to process <%s>', message)
                dest = ERRORS
            message.move(dest)


class InOutEmployee(models.Model):
    _inherit = 'hr.employee.public'

    hr_presence_state = fields.Selection(selection_add=[('present','In'), ('absent','Out')])
    io_punch_state = fields.Boolean('Punched in', compute='_compute_io_punch_state')
    io_punch_image_in = fields.Image('In', compute='_compute_io_punch_state')
    io_punch_image_out = fields.Image('Out', compute='_compute_io_punch_state')
    io_punch_ids = fields.One2many('in_out_board.punch', 'employee_id', 'Punches')
    io_phones = fields.Text('Phone', compute='_compute_phones')

    @api.depends('io_punch_ids.state')
    def _compute_io_punch_state(self):
        for emp in self:
            punches = emp.io_punch_ids
            emp.io_punch_state = state = (punches or False) and punches[-1].state == 'in'
            emp.io_punch_image_in = green_circle if state else blank_circle
            emp.io_punch_image_out = red_circle if not state else blank_circle

    @api.depends('io_punch_state')
    def _compute_presence_state(self):
        super()._compute_presence_state()
        for emp in self:
            if emp.io_punch_state:
                emp.hr_presence_state = 'present'

    @api.depends('work_phone', 'mobile_phone')
    def _compute_phones(self):
        for emp in self:
            lines = []
            if emp.work_phone:
                lines.append('w: %s' % emp.work_phone)
            if emp.mobile_phone:
                lines.append('m: %s' % emp.mobile_phone)
            emp.io_phones = '\n'.join(lines)





green_circle = (
        b'iVBORw0KGgoAAAANSUhEUgAAAJUAAACVCAYAAABRorhPAAAABHNCSVQICAgIfAhkiAAAEypJREFUeJztnWtTG9mZgB/RdEtISFiIi7DByGAuaw9g'
        b'7Ckcj8fjcdnxxp5bZWZTcc2Xrdraf7Af91/sp61K1c7u1iZxUjvXTSaZjB2HTDzOeAy+EwwDCAMWBoFAQnfavR9wawBLIEAISZznE2Wa1qF4/J63'
        b'33PO2wZN0zQEggxStNMDyHViapyYGt/pYeQVxTs9gGyjobEQCxNajABgLjYBMBn0ElfjhNQInsA0gWgw6c9Xl1ZQZirFLJlwmO2Jnw8tRpAMRdgU'
        b'C7JUjAFDdn6hHKSgpYqpcaJqnNBiBH90AYDHfg8PpgcYnfMwG5zkqf8pvqh/xc+F1fC69y6RShJfV1mrKbc6aXM0ssdURoezhTprDf7oAjZjKXaj'
        b'FUWS0dB2hWyGQsup9EgES9FjcNZNz+TDhETxaJjZqD8h0kLUj6qpK+4hGaSU9199LYAimxKS2Y02yo02yiwVlJvtHKpq4Uh1K1UWB0ZJwSjJKJKc'
        b'qV83J8l7qTQ04uoivmiAmZAPT9CLe26Cr9x/4fbkPdTFeFIRYG15NsNan1NqtNG6t4Pz9Sc4Ut2KLMk4LRWUKksyFlIEy0updJGiapwxvwdP0Mud'
        b'yT663dcZ9g4m/riZlmYrLBeuzGSntbKJU65X6XC2UKZYcVoqCiaK5Z1UGhoz4XmmgjN4gl4+fPAbRmaHeRJ6irqYX09pUrFMp7Odzn2dHHMeptpS'
        b'Qb2tJu8T/byQavkU92B6kDuTffSO3uSvk70AKEVyTkWldNGjV+xZnFKjlc66H/Be8znsJhsdVa0YJTkvBctpqfSkezLo5dsn97nlecjfPHdxz48C'
        b'uTW9ZQJVUykz2amyVnPadZLj+zpodTRgUyx5NS3mpFR6ZPLHgtydesS14ev0jPcUrEzL0aOXIps4WXuCY7WddDhbaLEfoFQpyYuolZNSxdQ497wD'
        b'dLtv0u2+zuB0P1DYMiVDj1ytlU2cP3iWswdOJGpeuUzOSBVT4/hjQdz+CT7p+4IrQ9eYj/iA3SfTalRNRTJINFQ0cbbxNBcbT+d0Qp8TUulC3Z16'
        b'xIcPfkOv5w4Lq6rcux1VUxNF1nONZ/jHI/+A01KBVTHv9NBeYEel0nOn73yP+cX9T+kZ72HMP574nyl4EV2uTmc7p1yv8mbT61SZ7TkVsXZMqpga'
        b'Z9TvoX9mmMu9v+Kvk715WxrYCfSE/kLr27zbei6nnhJ3RKqYGscXDXC577dcHepm2DuY7SEUDFKxzMnaE7zf8WOayl1Um8t3ekjZl0p/svuk7ws+'
        b'fPgRIBLxrRJWIxyubuNs42kuHXpjx6fDrEmlL6/cmLjDhw8/45uxm4AQKlPoudZbzRcTSfxO1bWyIpU+3f1m8E982v85g9P9QqZtQiqWeav5Imca'
        b'TtJV07YjT4fbvklPQ8MXDXB15IYQKgvE4hGuDF1jPDyLUZLpqGrNuljbHqkGfY/58+Nb/OzbD5iP+IRQWULVVI5WtXHp6E95fX9XVsXatkiloTEV'
        b'8vFfd/43UR0XQmUPySDRO3UfesEsl9BR1UJFyZ6sfPa2naZZiIW5OnKDK0PXWIj6hVA7gGSQeOAb5LeD3dydepS1U0EZn/40NL7zjfHZwFU+uPWf'
        b'ojqeA4TVCJXmKv719X/h7w+c3PYCaUYjlT7lfT7UzZWBK0KoHKFEMjEf8fHhw8+45x3AG57b1s/LqFQz4Xmujtzg93/7Pe75USFUDiEZJG6N9/BJ'
        b'3xfbPhVmJFHXz9fdmLjDv934d5GU5yiqpvJJ36eM+8cpM5XSXtG8LVNhRiLV0raVfi73/koIlcPofxc9Yo36PcTUOBqZrSplRCq3f4KP+q9wd7pP'
        b'CJUnXBm6xrdP7uOLBjK+lLPl6c8bnuM/bl3m+viNTIxHkCXmIz4uP/gYgLeazmS0OLrpSKWpKk9Ds/z84f9xbeRa3p252+1IBonB6X4uP/iYPz2+'
        b'SSAWyti9Ny3VghplLODh9sTtjA1GkH2mAk/5ZqyXyaA3Y/fctFRjfg+f9H3BrfEekUflKZJBYiHq58rQNf78+FbGygybkuppaJZf3P+UK0PXUjal'
        b'EOQP8xEfP/v2A2567uMNz235aXDDUmloS+15xntE+aBAkAwS8xEfPZMP8UW2foppw1JNhXx81H9FVMwLkF/e+TWfD3Un+nttlg1JFVPj3Hxyj6tD'
        b'fxBCFRh6fvXLO79m7HlRdLOkLZV+pOrDh5+xEA1s+gMFuc10aIrfDf0Zfyx5z9N0SFsqXzTAt0/uc3vyHiWSadMfKMhtlCKZbvd13P6JTUertKSK'
        b'qXEeTA9y+cHHxOKRTX2QID+QDBLD3kG63TfxRQObEmtdqTQ0omqc3w52MzrnFrnULkDVVLrd17n55B7R7ZAqri4yGfTytfsrsRSzS5AMEqNzbr4Z'
        b'6030m98Ia0qloeGPBfls4CrToalND1KQf8TiEXrGe7g6cmPDU+CaUsXVRaaCM/SO3kQp2vnGD4LsIRkkxvzj9E092vCT4JpS+WNBvnR/zZB/fEsD'
        b'FOQnqqZyb6qP/pnhDUWrlFJpaEwFZ7g9cVssx+xS9O0xj2bcRDewQzSlVHF1kS/dX9M/Ldr87Hb++OhLxvwe4upiWtenlMofC/Lo6YCIUrsc/UCq'
        b'J+hNu7yQVCoNDbd/gvEFT0YHKMhPFqIBHkwPMBn0pjUFJpUqri5yfayXYe+giFIClCKZq0PdPPanF2RekEpv/TMdmCasiiUZwRJTgae45ybSyquS'
        b'Rip9E56oTQlgKa8Kq2G+mujFl8YOlRekiquL+CJ+BnzfialPkEBdjHN77K+JN7yuxQtS+aIBBmZGtmVggvwmFo+kVQhdIZWGxljAw/3J+2LqEyRl'
        b'YGZk3dLCCqkMGJiPLHB78t62DkyQvwx5h9e9ZoVUgVgI99wEC9GAyKcESRmZHV53D/sKqSaDXkZm3ds9LkGeMzQ3tuYUuEKq+ViAe1N9Ip8SJEUy'
        b'SDwJPWV4boyoGkt53QtPf1OBp9s6MEF+s/C8ML4WKyNVZIGwGhb5lGBNZkM+VO1Zyu8npIqpce5M9mVlUIL8RSmSmQ96GZx1p1xcTkjljwUZ8g6L'
        b'ww2CdZmN+nk870l5PD4hlao9E1tdBGnhi/qZDs+m/H5CKslQJJJ0wbroi8uL6iLGFJ2NE1IZJUUcwxKkxUI0gC/kQ5aSt4xNSLWZQ4OC3U2qvVUJ'
        b'qcYCIp8SpM9syJdyb1VCqvnI+vtkBAJYKiuEFoMp91Z9P/3Ft9Y9TbD7iKdY/ysC/eBo6kdEgWA1sxE/s5H5pN/btpdICgqfVDsVimApi1+Ib74d'
        b'n0CwnCJIbZxAsBnE9CfIOEUApUoJpbJlp8ciKBBEpBJsmjXX/gwYqLKUZ3VAgvym3GSj3FSW9HuJSGU32bI2IEF+E3sWx1xsQV5vl4JJNmZtUILC'
        b'wGYsTfrvCanqrDVZG4wg/yk32zEXJ3/zR0KqVBcIBKkoVUqS/ntCqqgao9JclbUBCfKXUqMVu9m+/n4qVXtGlbU6awMT5CeqplIilVAsFa+99gdL'
        b'e9QPOpqRisXpZMHa2I02KktSl6BW7FHfZ63MyqAE+U250cb+spr1Dz5YFTPNjgNZG5ggP4k9i1NmqaDaUoGynlQAjXvqKJFKxBvcBSlRimTKzXac'
        b'loqU16yQKqRGRLIuWBNFNmE329e8ZoVUZYqVg45mYs/E/irBi+hPfuulSSukcloqOFx5cFsHJshvqqzVtDoaUibpsEoqq2LGtWcfpUaryKsESakt'
        b'rcG5RpIOSfZTlZlKecnetK0DE+QvjRUN617zQsvrOmsNR+u7RF4lSMoR56E1pz5I0vLabrSKepUgKYpsYr+tZs2pD1JsJ7abbFSaq0ReJUggFcvU'
        b'73Gl3EO1nBekUiSZpnIX5xrPbMvgBPmHXkq49NKP09oilTxSGa0cKHehyGKPlWCJ1som9pfVpNxDtZykUslSMS0OF3vN1WIKFBB7FqfN2Ub1Gksz'
        b'y0l5RKvV0cCB8gbR/lpAqdHKEechnJYKDBjWvT6pVAYM2BQLx2o7KTXaRLTaxaiaSqeznf221FtdVrPmYdIT+zporRSF0N2MZJA45XoVp6UiZY/P'
        b'1aSUSpFkHGY7bc42ykx2Ea12IaqmUmerpcXhwijJaU19sE6kshutvN18VkSrXYoimzjXfI5WR8O6Bc/lrCmVIsnYTTY693WKZZtdhqqp7DVX0+w4'
        b'gE3ZWPOWdRt02BQLP3S9QqnRuukBCvIPySBxrPYYrY6GtHMpnXWlUiSZOlsNbzVfFCdtdgmqptJReYjjdUfTLiMsJ61WQkZJ5kzDSer3uETCvgtQ'
        b'ZBNH67vo2tuedhlhOWlJpUgyL1U28U7rRbF0U+Comkr9HhfH93VgN1o3lKDrpN30zG608tr+l+l0thNWxStHCpXYszinXSc3/MS3nLSlUiSZelsN'
        b'7x1+W/RcKFCkYpnD1W283XwWR0nyhmbpsKH2jIok0+po4GjNEZFbFRj69pbTrpPYTbYNJ+fL2XDPz4P2Ot576U1cZfVCrALjXOMZLjS+RkXJni3d'
        b'Z8NSGTDQUdXCueZzYvmmgGiqbOX9tneos229+d2muhPbFAvH93VwtObIlgcg2HmkYpnTrpNUWRybKiGsZmOl0ucokkxXTRsA80EvvVP3xb6rPETV'
        b'VBTZxNnG87zdfHbL057Opvuoy1IxrY4GLh39KWWmtc/WC3ITySDRWfcD3m09t2bDjY2yaan0jXxde9s5WnNELOHkIQ0VTZzad5RWRwNWxZyx+27p'
        b'jQ+KJFNtLuf9jh9zsvaESNrzBFVTKTXaeKf1Im82vZ6xaU9nUznVajqqWjG9fAmAayPXRH6V4yiyiZ+0vcubTa9TZdx8kTMVGXk3jVGSabEf4ELL'
        b'WVxl9Zm4pWCbkIplOp3tnHZ1YTdaMUiZDwAZkUqRZEqVErr2tnOu+Zw4LJGjhNUInc52zh88S4v9wKbX9tbDoGmalskbesNzfDrwR/746EvuTvdl'
        b'8taCLXK+5Q3++ch71NlqMpqYryYjOdVyHCVlvLb/ZRbiQYb848xHfCLHygHqbLWccXVRZ0vvlPFWyLhUBgzU22q42HiaRXWR/77zc9RFsb99J9BT'
        b'kOMNr3O+/gQn9h3Z1gilk/HpbzlPQ7P8z/1P6XZfZ3C6X0SsLCMVy5ysPcE/vXyJFvuBrAgF2xCpllNltnOh8TWKpWLisTDu+VEhVhbpdLZzoeVs'
        b'VoWCbZbKgIGD9v2Jlw3+8s6vRY61zejrefV7XJw/eDZrU95ytnX604mpcXzRAFdHbvCH767y1eh1lCJZyJVhdKHear7ImYaTdNW0UaqUbGnD3WbI'
        b'ilQ6gViIu1P9fNR/ha/dX7EQ9Wfro3cFdbZafvR3P+LSoTewG63IUnHWhYIsv+3d+Hw78htNp3nFdQpAFEkzgKqpNFQ0caz2GD90vZI4BbMTQkGW'
        b'I5VOTI0z6vfw+VA3V4e6GZ1zE4tHxHS4QVRNpcxk5xXXKd5oOs1LlU1Um1O/Mi1b7IhUsNReeyrkY3DWzS/ufsz18RuinrUBpGKZEqmEn7S9y4XG'
        b'1xJFzZ2KTsvZ1qe/tdDba3dUtRJ96U1CBo3+J3eZj/gARNRKgaqpSAaJ+j0u2qsOcaHxtedP2DuTPyVjxyLVcvTpsH9mmN89ukqv546QaxX6k91e'
        b'czXHao/xfts7VFkcGd8LlQlyQipYmg4XYmEe+Ua4PtbLzeGvxdoh3z/IlJnsnGs8w/G6pZ2a9Wk0yd8pckYqneVR65uxXnrGexjzj+/0sHaMUqON'
        b'RlstR+u7OO3qwmXbh02x5KxQkINS6QRiIUKLEW4+ucc1903+5rnLgO+7gi+a6pFJkU10Ottpc7ZxxHmIjqqWnJdJJ2elgu+nxMmgl/6ZYQZmRuh2'
        b'X2d0zl2wT4qlRhutlU2ccr1Kh7MlLyLTanJaKp2YGscfC+KL+Pn2yX36ph5xb6qvoORaLlOVpZyuve2Yi005UybYCHkhlU5MjRNV40wGvTz2e3DP'
        b'TfCV+y/0Tw8mnhZ1cnWKXL6CIBkkGiqaOOho5nDlQVocrudv/VTyUiadvJJqORoacXWRUb+H+ViAu5OP6Bm/zfiCh3gsjC/qz5m1Rb0cUCKVYDfa'
        b'qLZVU2ur5XjdURr31OEw23d0rS7T5K1UOjF1afrzRQOMBTx4AtMMz41xe+I2/dODhNXw0nXxFxu1ZTqarV7HlAxSovJtN9qodhzg1L6jtDhclJvK'
        b'qLI4Ep1/8ylnWo+8l2o5evTS86/5WABPYJqBmRGGvMOEFoPMRvyJSBZWw8TikRXtvJWi9P64q39GP/pvN9ooN9oos1RgMlqp31PDMedhyk1lyJKM'
        b'01KxYo94IUSm1RSUVMnQ93IB+KMLCdGG58ZYVBfxhZZysdmQj9BicOnr5+KtRlZKsBpkZOOSFOUWJ+bn7aDtZjt7TGVUWcoTUxqAZCjCUVJWkPKk'
        b'ouCl0lj69fQ/6vInSQCbsRR/dIG4Gmc2Mk9UjROKhwlEg0nvZzVasJtsmGQjZYo18fP6vZY/sa3+7N1CwUu1EfTpUyeqrixXLO/dVChJ9XYgpBJk'
        b'nP8Hcx8+SIKJ4BwAAAAASUVORK5CYII='
        )


red_circle = (
        b'iVBORw0KGgoAAAANSUhEUgAAAJUAAACVCAYAAABRorhPAAAABHNCSVQICAgIfAhkiAAAFBNJREFUeJztnWtwVGWax//nvKfPOd2nO52LhMRcIECa'
        b'iIEJ4HglYBQvoCOLuGNRjrs1ly9bO7O1tVu1n3ar5ttO1X7ZcqhaL6NbO2opo4ziCqKoCISLjmIWI4QoAUkwAQzpTvfp7nP6vOfsh9MdknQn6SR9'
        b'z/v7lDqXzpvkn+d53ud93uflLMuywGBkED7fAygWzKgGi9J8D6MoEPI9gHxhUQozpAKGYV8Q7F9F7MoVWOEIzMAo6PAwTFVNftkhglR4IVRWgfN6'
        b'4KiqGnsfhgEIAjhJAi9LOfppCouSFtV4y2KGVNDrIwAAGgjAuHIF2tc9iPX2InbxAozLl2GODN94Nxqe8fM52XXja0kGqamFY9lyCE1NEOvrId++'
        b'HsTrBQCQMg/4cu+N5wmZ989XqHClGlONt0R0NAitt3dMRMbwNdDACBAIgv7wAywtaotI1wAyh/8zatjvEQLeWwnOpYAvKwO5uRZC1SLw1dWQmpdD'
        b'vuPHtlUDwJd7S1ZYJSGqhEWyYgYsVYXeP4BY3wXoPecQ2rcPsXNfA5GI/Uw4DM4VtzCEHxNDxkhYR2oA1Jx4j/AgS1ZAalsLz/ZtcDQ02O5z8WLw'
        b'bgVAaViwohZVQkymPwC97yJi/f1jQtKPHwEAcB73DeuT7z9YQnC6DiscBlnWDHHdOrgfeAjiymbIravAKQo4h1DU4ipaUVmU2mLqH4DW0wt1335E'
        b'j3fCDFzP99BmDSe7ILaugefxHRBXNsPR2AChtgacQwAIDw5cvoc4K4pKVBalsGIGjMEhaL29CB86gsipz6Af/ADAOKtUbP/llI5ZL66qCu4ndsJ5'
        b'7yZIy5dB9K0A71aKynIVhagSQXfsyhVEPulE9NQpRI51wujusoUkltDUPS4wvqYOZHkTnHdugOehByC1+MApSlGkKQpaVAnLZKkq1MNHETr8CfST'
        b'nyJ29iv7gVIS02Ti4uIqquDs2AxXezvk29dDallZ8DFXQYuKBkYR7TqN0EeHEHn/PcS6/8+esZWymCZDKSy/fyyo9+7cCWVTu53zKtB4q+BEZVGK'
        b'2KUB0B+G4X/xvxF68zU7HbDQxDSZcZYrEdQrD9w3FtAXkuUqqIx6YkanHvwY4aNHETn0of3LdDrzPbT8QwjgdMJSg9A+Pwlz5DpoKAT3ow9DbGwE'
        b'UDg5roKwVIlAXO/9FqN73kLojd12aoDS4pvJ5QJKAWqAK6uAs2MzPNu3QV7bBkdjfUEIK6+iSgTiWs85RD/7AoEXX4D+2Qlw5eVMTOkQj7f4ugYo'
        b'j26D9+mnILWuynsKIq/uz4oZ0C9dgrr/AEJ730bs7Ffg4mtjjDQgBFxVFaxoGKHdr8CSBFSIT0P0rQDxluVtWHmxVAl3p3WfQeDlVxF8blfp5Zty'
        b'TTyQl9o74Hl8B8p2bMvbonXORZUIxkdeeR2RziOIvLmbubtMomuAKKHin/4FytaHIbWszHnCNKeiMqMajMEhqAc/xsjvnwEd7GfBeDbQNfCLauF8'
        b'9BFU/Cz37jBn5cQWpXZm/ODHCLz4Amhfr32DCSrziBLMa4MI79mD0T1vQes+k9NS6JxYKjOqQes5B/VwJ/z/8TtYI8Ms95QL4q5Quu1O3PRv/5qz'
        b'mWFWRTU+ZeB/9gWo7+6FpQaZdcol8QBe3voTVP7615Db1mRdWFlNKSTKVNT9B5ig8gUhgChCO3EcgZtrwbtckNf9KKvfMmuWyqIUkZN/gf9PuxF6'
        b'5j/ZDC/fxLPwZMkK1L70IqTVt2ZtVpiVQD2xKBz8330I79nDBFUIEAKIEmhfL64/swtazzmYUS0r3yrjokrkocKdxxB85X+Yyys0RBGRQx9i9PU3'
        b'oH31dVZmhRl1fwlBBfcfwPBvfwvz2iDLkhci8Vmha8tjqPznf4S8+taMBu4ZDdTNkIrg/gPwP/sczKHLLG1QqIgSQKltserqQLxeCLU1GYuxMub+'
        b'zKgGrfsMgu+8g1jX50xQhQ4hsEZHoO57F9Evu2CpasZcYcZEpV+6hMDLryJ66ENAFDP1sYxsIkowurvgf/4FRLvP2Du6M8C8RWVGNdDh6wi89EcE'
        b'n9vF1vKKDK6qCtrxwxj+998hfPLTjFireYvK0jTo/QNQ970b33fHBFV0EAF692mEDx2B6Q/MW1jzEpVFKbTuM/A/G18gZjO94oQQWGoQo3/4L6iH'
        b'j87bDc5ZVGN1Uc8+D/XdvSyOKnYIASIR+J9/AVr3mXklRucuqpiBaPcZhPe+YbfhYW6v+BFFxL7pRfjzUzAGh+b8MXMSlUUpjMEhXN+1C1YwNOdv'
        b'zigwCIE5dBmhP+2GevDjOVurOYnKDKkIdx6DduK4va7HKB2cTsS+OoXQwfeh9ZybU9A+a1GZUQ3RrtMIvvOOXWzH3F7pQQRoJ45DPdwJM6TCwuxW'
        b'8mYtKktVEfroELQTx1lwXqoQAmtkGJHOI9B7v03uCDgDsxKVGdUQ3H8A6lt/hjU6wqxUKeN0IvLmbqhHj9nWahZuMG1RJYLz8Od/gdHdxXJSCwDO'
        b'5UJoz5vQe7+FFTPSfm9Wlip2qR/6yU/tzDmj9BFFxM59Da2nB1aqfvJTkJaoEonO0HvvQ//sBLNSCwVCAF2Df9cuqIePpv1aeqKKGdD7LiL0xm6W'
        b'QlhoEAGx872IdJ0GDYym9UpaojIGh6AePQba9w0Lzhca8b+3+tafQa+PpBWwzygqi1IY3w8i/MH7N5raMxYcRncXol92pTUTnFFUZkhF+PARxL7p'
        b'ZXmpBU7wrb1j5/tMx8zuzzAQ2vu23dmOub4FC+dyIdZ3Hlpv74ylMTOKSu8fsGd8jIWNKIIODSJ87OSN4+ymYFpRmVENo6+/kdGxMYqUeAVD5GQn'
        b'9L6L08ZVM1uq89+wAJ1hQ3iYg1eh9fRM6wKnFJUZ1aB99TXopUt2D3MGQ5RAB/sROTZ9ODStWtSjxxA73zu3gxUZpUkkgtjFC/axwFO4wClFZakq'
        b'9O/6YA2zminGOAgP4/Jl6N1nplxkTikqi1JoPb2g3w+yeIoxESKADvZDv3hpykemtFTa12ehnzrFEp6MiRACa3gY9OpVWFrqGvYpRaUPDLC1PkZK'
        b'OJcLWteX0Hu/Tbk5IqWoTH8A5tWrWR8co0iJx1XG9eGUt5NEZVGK8OdfQOvrZfEUIzXxxh50JJDydpKoOEJAr14DPX+BxVOMaTG+H0xZEZp69hfR'
        b'ivLUdEZu0b/rQ2x4OClfldL96QMDLD/FmBbO5YJx7hvELlxMylcliYoF6Yy0iAfrAMA5Jq64JIlK7x+AMXyNBemM6SEC6MBFWGo46VaypQqMskVk'
        b'xswQAsvvh6nHkm4liyoagXF5gC0iM9LC+H4wqQwmSVS87GSNNxhpQ/3+pErQ5DyVIMAKJ/tJBmMynMsF8+pV0NHghOtJoqKh4ORLDMaUmKoK+sPE'
        b'5ZrkPFWKaJ7BmA5L1yckQCeIyqIU9AeWSWekCeFBr9k5zfFn20wUVcwAjURyOzBGUWMGg7BmCtQZjPmSLKocngrOKE2YpWJknCRRETfrkseYHxNE'
        b'NXm1mcGYEUVOujRRVISA3FSZs/EwihxqwrG4zl6FmSpPBQCkqiqn42IUP5woTp2nAuy1PwYjXXhFAef1TLw2+SHLMFiBHiMtrHAYfHU1HJO8W8p6'
        b'Kr6mjuWrGGlBqqoAYYZyYl52gtx0E0DT7/DPWLgIleXg3cqEa8mi8paBr6ic9SE3jAUGpeBcLjummlTQmSQqsaEejqVNrFCPMT3UgKP1R+AUV1I/'
        b'heTZn6KAr67O2dgYRQo1wVdUgpedSbdSxFQSxPp6dqgRY1qscBiOpU3gvWUz7/sDAK7MA7JkBaDP/cRvRukjr1sHsWnpzDGVRSlIhRd8WVmuxsYo'
        b'UrgyDzgp+US1lF1fJJ8P0uo17CR3RmoohdDaBlLhTXk7pfsTm5aAr65mmXVGanQdjpaVEBYvTlnZMmUjWbG+nmXWGSmxwmGIy5shNtQnxVPANJWf'
        b'0q23wNHsA3Q9qwNkFBmUgisvB6muBqcoKR9JPfsjBFKLD8LKZpYEZUyEGiD1SyEubZzykSktFacoEJc1g6uqYi6QcQNqQqirg7y2DZycun3ntBsf'
        b'pJZmkNoGtrjMuIEogiyqBqmsAAcu5SNTioqXJSibNkJqW8sWlxk2ugZSvxTKg5tT5qcSzLhFS2hii8uMGwh1dZBWt067SWZaUXEOAe77O1i+imHP'
        b'+soqILWtBfF6U6YSEkwvKkIgt66Co+02cDIT1oJG1yEsaYKrYyNIZcW0j868Q1kQ4N7xBDhJZrPABYwVDkNavQaSz5dU6TmZGUXFuxU4169liVAG'
        b'lAc3z2ilgDRExRECR2MDXBs3soB9AUOWNUNsXQXenVw+PJm0GnQItTVQtj4M8fa7WI3VQoNScLIL3l/+CmJj44yCAtIUFecQIDbUw9lxPyuHWWhQ'
        b'A8KSJkjr14KXp85NjSc9URECTlHg6tgIobWNWauFAqUAEeD+6ZOQfL60X0u7PxUvS5B8Psj33TuH0TGKEl2HdMc9UDZtgFBbk/Zrs2p6JtTWwL3p'
        b'XjhuWc2sValDKSCKcG3Zatehz6LN1KxExcsS5LVtcHbcD4gSy1uVMtSwrdTdd6Y14xvPrNszCrU1cG95CHLHZlh+/2xfZxQD8SUZ15atEH0rZn34'
        b'1axFxcsS5LY18Ox4AmRZM7NWpQghkO66G+4tD9hWaooSl6mYUyNZ3q1AavFBXLeOWatSQ9fgWO6Dc8NGOBYvnpXbSzAnUdnlxivh3bmTVYaWEnG3'
        b'5972V2NWai7MueU15xCg3N8B5amnwVcuYsIqBXQdzo7N9upJmtnzVMxdVISAkyR4tm6FuG4dW2wuduJGwdXeDrGhPu3seSrm1eAzUXJM3B4M9ZwD'
        b'7esFnMldQBgFDqXgFA+UJ7ehbMc28OWpdx6ny7xPfOAcAqTWVSj7+S/Y5tNiJCGoR7fB+/RT4Munr+pMh/mLihDwbgXKfZsg373BPiaXCat40HUI'
        b'q26B8uBmSC2+eQsKyNDZNInZYNnPdkK67U4WXxULuga+pg7lT/8tlE3t83Z7CTLWND0RXwGA3+NG9P199lIOozChFPyiWnj//jdwbbgnI24vQUY7'
        b'8XMOAa7b1oNevYZYzznQ775lwipEKAVfuQiuBx6Cct8mCLU1GRMUkOGj2cbqrjbcg7KdO+1NqKyaobCgFNB1yHdvgHv7Y5BaVs4rfZAKzrIsK6Of'
        b'GIcOX8fIc39AaO/biPWetQN4RkFQ9qu/g/cXfwNp+bKMWqgEWTuIhlMUuDZtBB0N2qKilAkrn8RTB8KSJnh+8gjExsZZVx+kS9ZExcsSpNZVdp9t'
        b'vx+hN1+zXSGLsXJP/B/a2bEZyiNbIa9fC84hzLr6IF2y5v4SWJRCO9+HwEt/ROToEcS6PmdZ91wSF5T7iZ0o/+XPIfpWgHiz2yQ46+ewcYRAbGxE'
        b'2Y7tINXVCAwNwrw2yCxWLoi7PLF1DdzbH4PoWzHnyoPZkJPD/XhZgrT6VnBeD6jfj9CrLzNhZZt4qOHs2AzP9m1QNm3M+CxvKrLu/sZjUYrYpQGo'
        b'Bz/GyO+fAR3sZwF8NojYx+u5//pJlO3YnhOXN56cigqwhWWGVKgfHYL6wYd2AM/IKKS2ARW/+QcoD9xnJzZlMWtBeSpyfrZtYgFaXtsGTnHBGL6G'
        b'yJu77bNwmDucO/GkpuOeDXDfe/8NQWVxljcVObdU4zGjGrSec1D3H0Bo3z7Ezpy2bzB3mD7xihBO8cC1YwfKf/okpBYfSFVl3oaUV1EBtrCMwSFE'
        b'v+xC4LXXoJ04DksNMmGlw7iEpvP+zSh7fFtWll1mS96Pdudlye4qU9YOAAjKLoTfe8eevRCBiSsVlNodo4kAsXUNXFu2Qtm0AVLLylntJM4WebdU'
        b'CSxYADXHZofRU6cQPvg+zKHLgCgycSWIpwocK2+Fe8cTUO7bBLFpaU5ndzNRMKJKYFEK0x+A3j9gx1qffATjzFlYoyMLO5CPWyfH6nVwtm+E8/bb'
        b'IK9tg1Bbk3d3N5n828pJcISAL/dCUhRwLieEhnpEjp1A5Fjnws1r6Rr4RbVwNPvgeXwH5NvX2zteMlhYl0kKzlKNx4IFMxAEvT6CcOexMXEZ3V12'
        b'G+5SXkPUNVjBELiqKsgdm+G86x647vgxpDRbJOaTghZVgkTCNHblCvTuM4h0nUbkZCdip77I99CyhmO5Dw5fC1zt7WOWiVOUgnN1qSgKUSUwoxos'
        b'VYXePwDtq25Ejp2A1teL2Mnj9gPFOltM7D7SdfA1dZDv3gBXezuEJfWQfL4bScwi+dmKSlQJxluu2IWL0L74EuEjR6B3n4Y1Mmw/lChAK8TgPpES'
        b'SJz5Q/ixAFxctmyCZSomMSUoSlFNhgZGxwRmfDeA8NGjiPWdhzk6CnNk2E6mAvm1YuMy35wkg9TUgtxcC3F5M5y33wbHsqaCDr5nQ0mIyqIUVsw+'
        b'Ps4YHILx/aDtIs+cReRkJ+j5CzAD1+2HdW2Chci4y0y4svGWKJ5n42QXhLp6OHwtUB7cDEdjI3hvWVFbpVSUhKjGY8X/qFbMgKWqiA0PwwoEofX0'
        b'wOgfgHa2B/TaVZjB4A1LFg0DkciEwwc4l2v6Gu64YCa/w1VUga+oAu9ygq+oBFlUDa7SC3HJMjjXrwWpXQzeIYJUVowVzJWCkMZTcqKaikSQT0eD'
        b'MGO6LbTzfTC+HwT1+wFdB42EYF0PxJ8PgwZGADWa8vN4jwecxw1edoGr9II43QAAUuaB0FAPXlHsExIc4tj1UnBt6bBgRAXYVowjZMxdJkQ2HvrD'
        b'MCxdBw0FQUcCQCz1Fn5SvQi87ATvcoHzesbEA9gCgiCM5ZMS1nMhCApYYKJKh8QaJICxOG0qEou3C0Us6cJExcg4/w/BeLZH6KOntgAAAABJRU5E'
        b'rkJggg=='
        )


blank_circle = (
        b'iVBORw0KGgoAAAANSUhEUgAAAJUAAACVCAYAAABRorhPAAAABHNCSVQICAgIfAhkiAAAAZNJREFUeJzt0sEJACAQwDB1/53PJQqCJBP00T0zsyB0'
        b'XgfwH1ORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5'
        b'U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMV'
        b'OVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5Ez'
        b'FTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVOR'
        b'MxU5U5EzFTlTkTMVOVORMxU5U5EzFTlTkTMVOVORMxU5U5G7YhgFJpvHCA4AAAAASUVORK5CYII='
        )
